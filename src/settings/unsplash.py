from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class UnsplashSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    token: SecretStr = Field(validation_alias=AliasChoices("UNSPLASH_TOKEN", "unsplash_token"))
    max_connections: int = Field(
        default=5,
        gt=0,
        validation_alias=AliasChoices("UNSPLASH_MAX_CONNECTIONS", "unsplash_max_connections"),
    )
    timeout: int = Field(
        default=20,
        gt=0,
        validation_alias=AliasChoices("UNSPLASH_TIMEOUT", "unsplash_timeout"),
    )
