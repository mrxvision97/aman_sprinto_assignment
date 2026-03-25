from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sprinto"
    supabase_url: str = ""
    supabase_key: str = ""
    gemini_api_key: str = ""
    unstructured_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
