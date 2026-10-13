from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://spike:spike@localhost:5432/spike"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    ingest_hmac_secret: str = Field(min_length=32)
    max_body_bytes: int = Field(default=524_288, ge=1024, le=5_242_880)
    max_failures: int = Field(default=100, ge=1, le=1000)
    signature_tolerance_seconds: int = Field(default=300, ge=30, le=3600)


@lru_cache
def get_settings() -> Settings:
    return Settings()

