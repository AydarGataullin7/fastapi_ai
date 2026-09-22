import functools
import os
from datetime import datetime

import anyio
import html_page_generator._html_page_generator as _hpg  # noqa: PLC2701
import httpx
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient
from langchain_deepseek import ChatDeepSeek
from openai import APIStatusError

from src.env_settings import settings
from src.s3_client import upload_file_o_s3
from src.schemas import CreateSiteRequest, CreateSiteResponse, GenerateSiteRequest

HTTP_500_INTERNAL_SERVER_ERROR = 500

_hpg.ChatDeepSeek = functools.partial(ChatDeepSeek, max_tokens=65536)

_last_prompt = ""
_last_screenshot_url: str | None = None


def _clean_html(content: str) -> str:
    start = content.find("<!DOCTYPE html>")
    if start == -1:
        start = content.find("<html>")
    if start == -1:
        return content
    return content[start:]


_original_get_images = _hpg.get_images


async def _safe_get_images(keywords: list[str]) -> list[str]:
    query = keywords[0] if keywords else "abstract"
    try:
        return await _original_get_images([query])
    except httpx.HTTPStatusError:
        return []


_hpg.get_images = _safe_get_images


async def _generate_html(prompt: str) -> str:
    deepseek_limits = httpx.Limits(
        max_connections=settings.deepseek.max_connections,
        max_keepalive_connections=settings.deepseek.max_connections,
    )
    unsplash_limits = httpx.Limits(
        max_connections=settings.unsplash.max_connections,
        max_keepalive_connections=settings.unsplash.max_connections,
    )

    async with (
        AsyncUnsplashClient.setup(
            settings.unsplash.token.get_secret_value(),
            timeout=60,
            limits=unsplash_limits,
        ),
        AsyncDeepseekClient.setup(
        settings.deepseek.api_key.get_secret_value(),
        str(settings.deepseek.base_url),
        settings.deepseek.model,
        timeout=300,
        limits=deepseek_limits,
    ),
    ):
        generator = AsyncPageGenerator(debug_mode=True)

        try:
            async for _chunk in generator(prompt):
                pass
            return generator.html_page.html_code
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTP_500_INTERNAL_SERVER_ERROR:
                simple_prompt = prompt.split(maxsplit=1)[0] if prompt.split() else "site"
                generator = AsyncPageGenerator(debug_mode=True)
                async for _chunk in generator(simple_prompt):
                    pass
                return generator.html_page.html_code
            raise


async def _generate_and_upload_screenshot(
    site_id: int,
    html_code: str,
    gotenberg_client: httpx.AsyncClient,
) -> str | None:
    try:
        screenshot_bytes = await ScreenshotHTMLRequest(
            index_html=html_code,
            width=settings.gotenberg.width,
            format=settings.gotenberg.format,
            wait_delay=settings.gotenberg.wait_delay,
        ).asend(gotenberg_client)

        screenshot_path = f"screenshot_{site_id}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)

        screenshot_url = await upload_file_o_s3(
            file_path=screenshot_path,
            key=f"sites/{site_id}/screenshot.png",
            bucket=settings.s3.bucket,
            endpoint=settings.s3.endpoint,
            access_key=settings.s3.access_key,
            secret_key=settings.s3.secret_key,
            content_type="image/png",
            content_disposition="inline",
        )
        os.remove(screenshot_path)
        return screenshot_url
    except GotenbergServerError as e:
        print(f"Gotenberg error: {e}")
        return None
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None


router = APIRouter()


@router.post("/sites/create", response_model=CreateSiteResponse)
async def create_site(request: CreateSiteRequest):
    now = datetime.now()
    return CreateSiteResponse(
        id=1,
        title=request.title,
        prompt=request.prompt,
        created_at=now,
        updated_at=now,
        view_url="https://google.com",
        download_url="https://google.com",
        screenshot_url="https://google.com",
    )


@router.post("/sites/{site_id}/generate")
async def generate_site(site_id: int, request: GenerateSiteRequest, http_request: Request):
    global _last_prompt, _last_screenshot_url  # noqa: PLW0603
    _last_prompt = request.prompt

    try:
        raw_html = await _generate_html(request.prompt)
        html_code = _clean_html(raw_html)

        with anyio.CancelScope(shield=True):
            with open("index.html", "w", encoding="utf-8") as file:
                file.write(html_code)

            try:
                view_url = await upload_file_o_s3(
                    file_path="index.html",
                    key=f"sites/{site_id}/index.html",
                    bucket=settings.s3.bucket,
                    endpoint=settings.s3.endpoint,
                    access_key=settings.s3.access_key,
                    secret_key=settings.s3.secret_key,
                    content_type="text/html",
                    content_disposition="inline",
                )
                download_url = f"{view_url}?response-content-disposition=attachment"
                status = "success"
            except (ClientError, Exception) as e:
                view_url = "/index.html"
                download_url = "/index.html"
                status = "saved_locally"
                print(f"S3 error: {e}")

            gotenberg_client = http_request.app.state.gotenberg_client
            screenshot_url = await _generate_and_upload_screenshot(site_id, html_code, gotenberg_client)
            _last_screenshot_url = screenshot_url

            return {
                "status": status,
                "view_url": view_url,
                "download_url": download_url,
                "html_url": view_url,
                "screenshot_url": screenshot_url,
            }

    except httpx.ConnectError:
        raise HTTPException(503, "Не удалось подключиться к сервису Unsplash или DeepSeek")
    except httpx.ReadTimeout:
        raise HTTPException(504, "Превышено время ожидания ответа от нейросети")
    except APIStatusError as e:
        if "Insufficient Balance" in str(e):
            raise HTTPException(402, "Недостаточно средств на балансе DeepSeek")
        raise HTTPException(500, f"Ошибка API: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Ошибка генерации сайта: {str(e)}")


@router.get("/sites/my")
async def get_my_sites():
    now = datetime.now()
    site_id = 1
    view_url = f"http://localhost:9000/fastai/sites/{site_id}/index.html"
    download_url = f"{view_url}?response-content-disposition=attachment"

    sites = [
        {
            "id": site_id,
            "title": _last_prompt,
            "prompt": _last_prompt,
            "urlPath": f"/sites/{site_id}",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "htmlCodeUrl": view_url,
            "htmlCodeDownloadUrl": download_url,
            "screenshotUrl": _last_screenshot_url,
        },
    ]
    return JSONResponse(content={"sites": sites})


@router.get("/sites/{site_id}")
async def get_site(site_id: int):
    now = datetime.now()
    view_url = f"http://localhost:9000/fastai/sites/{site_id}/index.html"
    download_url = f"{view_url}?response-content-disposition=attachment"

    return {
        "id": site_id,
        "title": _last_prompt,
        "prompt": _last_prompt,
        "urlPath": f"/sites/{site_id}",
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
        "htmlCodeUrl": view_url,
        "htmlCodeDownloadUrl": download_url,
        "screenshotUrl": _last_screenshot_url,
    }
