import json
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.env_settings import settings
from src.schemas import UserProfileResponse
from src.sites import router as sites_router

print("📋 Настройки приложения:")
print(json.dumps({
    "DEEPSEEK_MODEL": settings.deepseek.model,
    "DEEPSEEK_MAX_CONNECTIONS": settings.deepseek.max_connections,
    "UNSPLASH_TIMEOUT": settings.unsplash.timeout,
    "UNSPLASH_MAX_CONNECTIONS": settings.unsplash.max_connections,
    "S3_ENDPOINT": settings.s3.endpoint,
    "S3_BUCKET": settings.s3.bucket,
    "S3_ACCESS_KEY": "***",
    "S3_SECRET_KEY": "***",
    "S3_CONNECT_TIMEOUT": settings.s3.connect_timeout,
    "S3_READ_TIMEOUT": settings.s3.read_timeout,
    "S3_MAX_CONNECTIONS": settings.s3.max_connections,
    "GOTENBERG_URL": str(settings.gotenberg.url),
    "GOTENBERG_WIDTH": settings.gotenberg.width,
    "GOTENBERG_FORMAT": settings.gotenberg.format,
    "GOTENBERG_WAIT_DELAY": settings.gotenberg.wait_delay,
    "GOTENBERG_TIMEOUT": settings.gotenberg.timeout,
    "GOTENBERG_MAX_CONNECTIONS": settings.gotenberg.max_connections,
}, indent=2, ensure_ascii=False))


@asynccontextmanager
async def lifespan(app: FastAPI):
    limits = httpx.Limits(
        max_connections=settings.gotenberg.max_connections,
        max_keepalive_connections=settings.gotenberg.max_connections,
    )
    async with httpx.AsyncClient(
        base_url=str(settings.gotenberg.url),
        timeout=settings.gotenberg.timeout,
        limits=limits,
    ) as gotenberg_client:
        app.state.gotenberg_client = gotenberg_client
        yield


app = FastAPI(lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

app.include_router(sites_router, prefix="/frontend-api", tags=["sites"])


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/frontend-settings.json")
def serve_settings():
    return FileResponse(os.path.join(FRONTEND_DIR, "frontend-settings.json"))


@app.get("/vite.svg")
def serve_vite_icon():
    return FileResponse(os.path.join(FRONTEND_DIR, "vite.svg"))


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
