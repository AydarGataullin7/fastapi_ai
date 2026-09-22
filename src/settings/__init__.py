from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.settings.deepseek import DeepSeekSettings
from src.settings.gotenberg import GotenbergSettings
from src.settings.s3 import S3Settings
from src.settings.unsplash import UnsplashSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    debug: bool = False

    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    unsplash: UnsplashSettings = Field(default_factory=UnsplashSettings)
    s3: S3Settings = Field(default_factory=S3Settings)
    gotenberg: GotenbergSettings = Field(default_factory=GotenbergSettings)


settings = Settings()
