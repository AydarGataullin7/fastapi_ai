from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    endpoint: str = Field(
        default="localhost:9000",
        validation_alias=AliasChoices(
            "S3_ENDPOINT", "MINIO_ENDPOINT", "s3_endpoint", "minio_endpoint",
        ),
    )
    access_key: str = Field(
        validation_alias=AliasChoices(
            "S3_ACCESS_KEY", "MINIO_ACCESS_KEY", "s3_access_key", "minio_access_key",
        ),
    )
    secret_key: str = Field(
        validation_alias=AliasChoices(
            "S3_SECRET_KEY", "MINIO_SECRET_KEY", "s3_secret_key", "minio_secret_key",
        ),
    )
    bucket: str = Field(
        default="fastapi",
        validation_alias=AliasChoices(
            "S3_BUCKET", "MINIO_BUCKET", "s3_bucket", "minio_bucket",
        ),
    )
    secure: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "S3_SECURE", "MINIO_SECURE", "s3_secure", "minio_secure",
        ),
    )
    connect_timeout: int = Field(
        default=5,
        ge=1,
        validation_alias=AliasChoices(
            "S3_CONNECT_TIMEOUT", "MINIO_CONNECT_TIMEOUT", "s3_connect_timeout", "minio_connect_timeout",
        ),
    )
    read_timeout: int = Field(
        default=30,
        ge=1,
        validation_alias=AliasChoices(
            "S3_READ_TIMEOUT", "MINIO_READ_TIMEOUT", "s3_read_timeout", "minio_read_timeout",
        ),
    )
    max_connections: int = Field(
        default=10,
        ge=1,
        validation_alias=AliasChoices(
            "S3_MAX_CONNECTIONS", "MINIO_MAX_CONNECTIONS", "s3_max_connections", "minio_max_connections",
        ),
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        if ":" not in v:
            raise ValueError("Endpoint must be in format 'host:port'")
        host, port = v.rsplit(":", 1)
        if not host or not port.isdigit():
            raise ValueError("Endpoint must be in format 'host:port'")
        return v
