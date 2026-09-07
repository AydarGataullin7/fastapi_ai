import functools
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

import anyio
import html_page_generator._html_page_generator as _hpg  # noqa: PLC2701
import httpx
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient
from langchain_deepseek import ChatDeepSeek
from openai import APIStatusError
from pydantic import BaseModel, Field

from src.env_settings import settings
from src.s3_client import upload_file_o_s3

print("📋 Настройки приложения:")
print(json.dumps({
    "DEEPSEEK_MODEL": settings.deepseek_model,
    "UNSPLASH_TIMEOUT": settings.unsplash_timeout,
    "MINIO_ENDPOINT": settings.minio_endpoint,
    "MINIO_BUCKET": settings.minio_bucket,
    "MINIO_ACCESS_KEY": "***",
    "MINIO_SECRET_KEY": "***",
    "MINIO_CONNECT_TIMEOUT": settings.minio_connect_timeout,
    "MINIO_READ_TIMEOUT": settings.minio_read_timeout,
    "MINIO_MAX_CONNECTIONS": settings.minio_max_connections,
    "GOTENBERG_URL": settings.gotenberg_url,
    "GOTENBERG_WIDTH": settings.gotenberg_width,
    "GOTENBERG_FORMAT": settings.gotenberg_format,
    "GOTENBERG_WAIT_DELAY": settings.gotenberg_wait_delay,
    "GOTENBERG_TIMEOUT": settings.gotenberg_timeout,
    "GOTENBERG_MAX_CONNECTIONS": settings.gotenberg_max_connections,
}, indent=2, ensure_ascii=False))

HTTP_500_INTERNAL_SERVER_ERROR = 500

_hpg.ChatDeepSeek = functools.partial(ChatDeepSeek, max_tokens=65536)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        base_url=settings.gotenberg_url,
        timeout=settings.gotenberg_timeout,
    ) as gotenberg_client:
        app.state.gotenberg_client = gotenberg_client
        yield


async def generate_and_upload_screenshot(
    site_id: int,
    html_code: str,
) -> str | None:
    try:
        screenshot_bytes = await ScreenshotHTMLRequest(
            index_html=html_code,
            width=settings.gotenberg_width,
            format=settings.gotenberg_format,
            wait_delay=settings.gotenberg_wait_delay,
        ).asend(app.state.gotenberg_client)

        screenshot_path = f"screenshot_{site_id}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)

        screenshot_url = await upload_file_o_s3(
            file_path=screenshot_path,
            key=f"sites/{site_id}/screenshot.png",
            bucket=settings.minio_bucket,
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
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


class UserProfileResponse(BaseModel):
    profileId: int = Field(description="Уникальный идентификатор пользователя")
    email: str = Field(description="Email пользователя")
    username: str = Field(min_length=3, max_length=20, description="Имя пользователя")
    registeredAt: str = Field(description="Дата регистрации")
    updatedAt: str = Field(description="Дата последнего обновления профиля")
    isActive: bool = Field(description="Активен ли пользователь")


class CreateSiteRequest(BaseModel):
    title: str = Field(default="Без названия", min_length=1, max_length=100, description="Заголовок сайта")
    prompt: str = Field(..., min_length=1, description="Промт для генерации сайта")


class CreateSiteResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор сайта в системе")
    title: str = Field(description="Заголовок сайта")
    prompt: str = Field(description="Промт, использованный для генерации сайта")
    created_at: datetime = Field(description="Дата и время создания сайта")
    updated_at: datetime = Field(description="Дата и время последнего обновления сайта")
    view_url: str = Field(description="Ссылка для просмотра сайта в браузере")
    download_url: str = Field(description="Ссылка для скачивания HTML-файла сайта")
    screenshot_url: str = Field(description="Ссылка на скриншот сгенерированного сайта")


class GenerateSiteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Промпт для генерации сайта")


app = FastAPI(lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

_last_prompt = ""
_last_site_data = {
    "prompt": "",
    "screenshot_url": None,
}


async def generate_html(prompt: str) -> str:
    async with (
        AsyncUnsplashClient.setup(
            settings.unsplash_token.get_secret_value(),
            timeout=60,
        ),
        AsyncDeepseekClient.setup(
            settings.deepseek_api_key.get_secret_value(),
            settings.deepseek_base_url,
            settings.deepseek_model,
            timeout=300,
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


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/frontend-settings.json")
def serve_settings():
    return FileResponse(os.path.join(FRONTEND_DIR, "frontend-settings.json"))


@app.get("/frontend-api/users/me", response_model=UserProfileResponse)
def get_current_user():
    return {
        "profileId": 1,
        "email": "mock@user.com",
        "username": "mock-user",
        "registeredAt": "2025-06-15T18:29:56+00:00",
        "updatedAt": "2025-06-15T18:29:56+00:00",
        "isActive": True,
    }


@app.get("/vite.svg")
def serve_vite_icon():
    return FileResponse(os.path.join(FRONTEND_DIR, "vite.svg"))


@app.post("/frontend-api/sites/create", response_model=CreateSiteResponse)
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


@app.post("/frontend-api/sites/{site_id}/generate")
async def generate_site(site_id: int, request: GenerateSiteRequest):
    global _last_prompt  # noqa: PLW0603
    _last_prompt = request.prompt
    _last_site_data["prompt"] = request.prompt

    try:
        raw_html = await generate_html(request.prompt)
        html_code = _clean_html(raw_html)

        with anyio.CancelScope(shield=True):
            with open("index.html", "w", encoding="utf-8") as file:
                file.write(html_code)

            try:
                view_url = await upload_file_o_s3(
                    file_path="index.html",
                    key=f"sites/{site_id}/index.html",
                    bucket=settings.minio_bucket,
                    endpoint=settings.minio_endpoint,
                    access_key=settings.minio_access_key,
                    secret_key=settings.minio_secret_key,
                    content_type="text/html",
                    content_disposition="inline",
                )
                download_url = f'{view_url}?response-content-disposition=attachment'
                status = "success"
            except (ClientError, Exception) as e:
                view_url = "/index.html"
                download_url = "/index.html"
                status = "saved_locally"
                print(f"MinIO error: {e}")

            screenshot_url = await generate_and_upload_screenshot(site_id, html_code)
            _last_site_data["screenshot_url"] = screenshot_url

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


@app.get("/frontend-api/sites/my")
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
            "screenshotUrl": _last_site_data["screenshot_url"],
        },
    ]
    return JSONResponse(content={"sites": sites})


@app.get("/frontend-api/sites/{site_id}")
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
        "screenshotUrl": _last_site_data["screenshot_url"],
    }
