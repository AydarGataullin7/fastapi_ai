import asyncio
import functools
import logging
import os
from datetime import datetime

import html_page_generator._html_page_generator as _hpg  # noqa: PLC2701
import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient
from langchain_deepseek import ChatDeepSeek

from src.env_settings import settings
from src.s3_client import upload_file_o_s3
from src.schemas import CreateSiteRequest, CreateSiteResponse, GenerateSiteRequest

logger = logging.getLogger(__name__)

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


async def _generate_and_upload_screenshot(
    site_id: int,
    html_code: str,
    gotenberg_client: httpx.AsyncClient,
    s3_client,
) -> str | None:
    try:
        screenshot_bytes = await ScreenshotHTMLRequest(
            index_html=html_code,
            width=settings.gotenberg.width,
            format=settings.gotenberg.format,
            wait_delay=settings.gotenberg.wait_delay,
        ).asend(gotenberg_client)
    except GotenbergServerError as e:
        logger.error("Gotenberg error: %s", e)
        return None

    try:
        screenshot_path = f"screenshot_{site_id}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)

        screenshot_url = await upload_file_o_s3(
            client=s3_client,
            file_path=screenshot_path,
            key=f"sites/{site_id}/screenshot.png",
            bucket=settings.s3.bucket,
            endpoint=settings.s3.endpoint,
            content_type="image/png",
            content_disposition="inline",
        )
        os.remove(screenshot_path)
        return screenshot_url
    except (ClientError, BotoCoreError, OSError) as e:
        logger.error("Screenshot upload error: %s", e)
        return None


async def _upload_site_after_generation(
    site_id: int,
    html_code: str,
    gotenberg_client: httpx.AsyncClient,
    s3_client,
) -> None:
    global _last_screenshot_url  # noqa: PLW0603

    try:
        with open("index.html", "w", encoding="utf-8") as file:
            file.write(html_code)
    except OSError as e:
        logger.error("Failed to write index.html: %s", e)
        return

    try:
        await upload_file_o_s3(
            client=s3_client,
            file_path="index.html",
            key=f"sites/{site_id}/index.html",
            bucket=settings.s3.bucket,
            endpoint=settings.s3.endpoint,
            content_type="text/html",
            content_disposition="inline",
        )
    except (ClientError, BotoCoreError, OSError) as e:
        logger.error("S3 error: %s", e)

    screenshot_url = await _generate_and_upload_screenshot(
        site_id, html_code, gotenberg_client, s3_client,
    )
    _last_screenshot_url = screenshot_url


async def generate_site_stream(
    site_id: int,
    prompt: str,
    gotenberg_client: httpx.AsyncClient,
    s3_client,
):
    global _last_prompt  # noqa: PLW0603
    _last_prompt = prompt

    deepseek_limits = httpx.Limits(
        max_connections=settings.deepseek.max_connections,
        max_keepalive_connections=settings.deepseek.max_connections,
    )
    unsplash_limits = httpx.Limits(
        max_connections=settings.unsplash.max_connections,
        max_keepalive_connections=settings.unsplash.max_connections,
    )

    chunks: list[str] = []
    background_task: asyncio.Task | None = None

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
            async for chunk in generator(prompt):
                chunks.append(chunk)
                yield chunk
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTP_500_INTERNAL_SERVER_ERROR:
                simple_prompt = prompt.split(maxsplit=1)[0] if prompt.split() else "site"
                generator = AsyncPageGenerator(debug_mode=True)
                async for chunk in generator(simple_prompt):
                    chunks.append(chunk)
                    yield chunk
            else:
                raise

    raw_html = "".join(chunks)
    html_code = _clean_html(raw_html)

    background_task = asyncio.create_task(
        _upload_site_after_generation(
            site_id, html_code, gotenberg_client, s3_client,
        ),
    )
    await background_task


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
    s3_client = http_request.app.state.s3_client
    gotenberg_client = http_request.app.state.gotenberg_client

    return StreamingResponse(
        generate_site_stream(site_id, request.prompt, gotenberg_client, s3_client),
        media_type="text/plain",
    )


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
