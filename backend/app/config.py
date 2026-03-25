from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _ensure_asyncpg_database_url(url: str) -> str:
    """Railway/Heroku-style URLs use postgresql://; SQLAlchemy async needs postgresql+asyncpg://."""
    if not url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "+" in scheme:
        return url
    s = scheme.lower()
    if s in ("postgresql", "postgres"):
        return f"postgresql+asyncpg://{rest}"
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprinto"
    # auto: no SSL for localhost; require SSL for remote hosts (e.g. Railway). Override with require/disable.
    database_ssl: str = "auto"
    supabase_url: str = ""
    supabase_key: str = ""
    gemini_api_key: str = ""
    unstructured_api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    environment: str = "development"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: object) -> object:
        # Empty env (e.g. broken Railway variable reference) would crash SQLAlchemy on import.
        if v is None or (isinstance(v, str) and not v.strip()):
            v = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprinto"
        elif isinstance(v, str):
            v = _ensure_asyncpg_database_url(v.strip())
        return v


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache():
    get_settings.cache_clear()
