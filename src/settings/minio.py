from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    endpoint: str = Field(
        default="localhost:9000",
        validation_alias=AliasChoices("MINIO_ENDPOINT", "minio_endpoint"),
    )
    access_key: str = Field(validation_alias=AliasChoices("MINIO_ACCESS_KEY", "minio_access_key"))
    secret_key: str = Field(validation_alias=AliasChoices("MINIO_SECRET_KEY", "minio_secret_key"))
    bucket: str = Field(
        default="fastapi",
        validation_alias=AliasChoices("MINIO_BUCKET", "minio_bucket"),
    )
    secure: bool = Field(
        default=False,
        validation_alias=AliasChoices("MINIO_SECURE", "minio_secure"),
    )
    connect_timeout: int = Field(
        default=5,
        ge=1,
        validation_alias=AliasChoices("MINIO_CONNECT_TIMEOUT", "minio_connect_timeout"),
    )
    read_timeout: int = Field(
        default=30,
        ge=1,
        validation_alias=AliasChoices("MINIO_READ_TIMEOUT", "minio_read_timeout"),
    )
    max_connections: int = Field(
        default=10,
        ge=1,
        validation_alias=AliasChoices("MINIO_MAX_CONNECTIONS", "minio_max_connections"),
    )
