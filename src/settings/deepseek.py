from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSeekSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    api_key: SecretStr = Field(
        validation_alias=AliasChoices("DEEPSEEK_API_KEY", "deepseek_api_key"),
    )
    base_url: AnyHttpUrl = Field(
        default="https://api.deepseek.com/v1",
        validation_alias=AliasChoices("DEEPSEEK_BASE_URL", "deepseek_base_url"),
    )
    model: str = Field(
        default="deepseek-chat",
        validation_alias=AliasChoices("DEEPSEEK_MODEL", "deepseek_model"),
    )
    max_connections: int = Field(
        default=5,
        gt=0,
        validation_alias=AliasChoices("DEEPSEEK_MAX_CONNECTIONS", "deepseek_max_connections"),
    )
