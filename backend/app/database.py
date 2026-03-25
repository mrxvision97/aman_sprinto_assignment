from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()


def _asyncpg_connect_args(database_url: str, ssl_mode: str) -> dict:
    """Local Postgres usually has no SSL; managed providers need TLS."""
    mode = (ssl_mode or "auto").strip().lower()
    if mode in ("0", "false", "disable", "off"):
        return {}
    if mode in ("1", "true", "require", "on"):
        return {"ssl": "require"}
    raw = database_url
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if raw.startswith(prefix):
            raw = "postgresql://" + raw.split("://", 1)[1]
            break
    try:
        host = (urlparse(raw).hostname or "").lower()
    except Exception:
        host = ""
    # Typical local/dev Postgres (bare metal, Docker Compose service names).
    if host in ("localhost", "127.0.0.1", "::1", "postgres", "db") or host.endswith(".local"):
        return {}
    return {"ssl": "require"}


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=_asyncpg_connect_args(settings.database_url, settings.database_ssl),
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

        from app.models import role, resume, score  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
