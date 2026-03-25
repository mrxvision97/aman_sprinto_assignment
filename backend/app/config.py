from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprinto"
    # auto: no SSL for localhost; require SSL for remote hosts (e.g. Railway). Override with require/disable.
    database_ssl: str = "auto"
    supabase_url: str = ""
    supabase_key: str = ""
    gemini_api_key: str = ""
    unstructured_api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    environment: str = "development"

    class Config:
        env_file = ".env"


@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache():
    get_settings.cache_clear()
