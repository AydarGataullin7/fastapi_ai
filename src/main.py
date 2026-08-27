import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    profileId: int = Field(description="Уникальный идентификатор пользователя")
    email: str = Field(description="Email пользователя")
    username: str = Field(min_length=3, max_length=20, description="Имя пользователя")
    registeredAt: str = Field(description="Дата регистрации")
    updatedAt: str = Field(description="Дата последнего обновления профиля")
    isActive: bool = Field(description="Активен ли пользователь")


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")


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
    return FileResponse(os.path(FRONTEND_DIR, "vite.svg"))
