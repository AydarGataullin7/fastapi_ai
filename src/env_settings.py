from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    deepseek_api_key: SecretStr
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_connections: int = Field(default=5, gt=0, description="Максимальное количество подключений к DeepSeek")

    debug: bool = False

    unsplash_token: SecretStr
    unsplash_max_connections: int = Field(default=5, gt=0)
    unsplash_timeout: int = Field(default=20, gt=0)

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "fastapi"
    minio_secure: bool = False


settings = Settings()
