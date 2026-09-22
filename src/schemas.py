from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field


class UserProfileResponse(BaseModel):
    profileId: int = Field(description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(description="Email пользователя")
    username: str = Field(min_length=3, max_length=20, description="Имя пользователя")
    registeredAt: datetime = Field(description="Дата регистрации")
    updatedAt: datetime = Field(description="Дата последнего обновления профиля")
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
    view_url: AnyHttpUrl = Field(description="Ссылка для просмотра сайта в браузере")
    download_url: AnyHttpUrl = Field(description="Ссылка для скачивания HTML-файла сайта")
    screenshot_url: AnyHttpUrl = Field(description="Ссылка на скриншот сгенерированного сайта")


class GenerateSiteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Промт для генерации сайта")
