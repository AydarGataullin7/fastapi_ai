from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GotenbergSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    url: str = Field(
        default="https://demo.gotenberg.dev",
        validation_alias=AliasChoices("GOTENBERG_URL", "gotenberg_url"),
    )
    width: int = Field(
        default=1280,
        validation_alias=AliasChoices("GOTENBERG_WIDTH", "gotenberg_width"),
    )
    format: str = Field(
        default="png",
        validation_alias=AliasChoices("GOTENBERG_FORMAT", "gotenberg_format"),
    )
    timeout: int = Field(
        default=10,
        ge=1,
        validation_alias=AliasChoices("GOTENBERG_TIMEOUT", "gotenberg_timeout"),
    )
    wait_delay: int = Field(
        default=8,
        ge=1,
        validation_alias=AliasChoices("GOTENBERG_WAIT_DELAY", "gotenberg_wait_delay"),
    )
    max_connections: int = Field(
        default=5,
        ge=1,
        validation_alias=AliasChoices("GOTENBERG_MAX_CONNECTIONS", "gotenberg_max_connections"),
    )
