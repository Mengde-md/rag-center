from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True
    )

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/rag_center"
    model_base_url: str = "https://api.openai.com/v1"
    model_api_key: SecretStr = SecretStr("")
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = Field(default=1536, ge=1, le=2000)
    embedding_batch_size: int = Field(default=32, ge=1, le=256)
    model_timeout_seconds: float = Field(default=60, gt=0, le=600)
    vector_store: Literal["pgvector"] = "pgvector"
    chunk_size: int = Field(default=800, ge=1)
    chunk_overlap: int = Field(default=100, ge=0)
    top_k: int = Field(default=5, ge=1, le=100)
    max_content_length: int = Field(default=100_000, ge=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            url = make_url(value)
        except (ArgumentError, ValueError):
            # Parser errors may include configuration fragments, such as a malformed port.
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy database URL") from None
        if url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("model_base_url")
    @classmethod
    def validate_model_base_url(cls, value: str) -> str:
        from urllib.parse import urlsplit

        message = (
            "MODEL_BASE_URL must be an HTTP(S) base URL with a host and valid port, "
            "without credentials, whitespace, query or fragment"
        )
        try:
            url = urlsplit(value)
            hostname = url.hostname
            # urllib validates malformed and out-of-range ports only when this is accessed.
            port = url.port
        except ValueError:
            raise ValueError(message) from None
        if (
            url.scheme not in {"http", "https"}
            or not hostname
            or url.username is not None
            or url.password is not None
            or port == 0
            or "?" in value
            or "#" in value
            or any(character.isspace() for character in value)
        ):
            raise ValueError(message)
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
