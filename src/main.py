import os
from contextlib import AsyncExitStack, asynccontextmanager

import aioboto3
import httpx
from botocore.config import Config
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.env_settings import settings
from src.patches import apply_patches
from src.schemas import UserProfileResponse
from src.sites import router as sites_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    apply_patches()

    async with AsyncExitStack() as stack:
        limits = httpx.Limits(
            max_connections=settings.gotenberg.max_connections,
            max_keepalive_connections=settings.gotenberg.max_connections,
        )
        gotenberg_client = await stack.enter_async_context(
            httpx.AsyncClient(
                base_url=str(settings.gotenberg.url),
                timeout=settings.gotenberg.timeout,
                limits=limits,
            ),
        )
        app.state.gotenberg_client = gotenberg_client

        s3_config = Config(
            proxies={},
            connect_timeout=settings.s3.connect_timeout,
            read_timeout=settings.s3.read_timeout,
            max_pool_connections=settings.s3.max_connections,
            retries={"max_attempts": 2, "mode": "standard"},
        )
        s3_session = aioboto3.Session()
        s3_client = await stack.enter_async_context(
            s3_session.client(
                "s3",
                endpoint_url=f"http://{settings.s3.endpoint}",
                aws_access_key_id=settings.s3.access_key,
                aws_secret_access_key=settings.s3.secret_key,
                config=s3_config,
            ),
        )
        app.state.s3_client = s3_client

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
