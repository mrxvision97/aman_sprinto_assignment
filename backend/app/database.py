import re
import socket
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()

# Supabase "direct connection" hostname — AAAA-first DNS breaks on hosts without IPv6 egress (e.g. Railway).
_SUPABASE_DIRECT_DB_HOST = re.compile(r"^db\.[a-z0-9-]+\.supabase\.co$", re.IGNORECASE)
_LOCAL_DNS_NAMES = frozenset({"localhost", "127.0.0.1", "::1", "postgres", "db"})
_orig_getaddrinfo: type[socket.getaddrinfo] | None = None
_ipv4_dns_patch_applied = False


def _is_local_dns_node(node: object) -> bool:
    if node is None:
        return True
    h = str(node).lower().rstrip(".")
    if h in _LOCAL_DNS_NAMES:
        return True
    return h.endswith(".local")


def _maybe_patch_ipv4_first_dns(database_url: str, enabled: bool) -> None:
    """Prefer A records for Supabase direct DB host so asyncpg/uvloop do not try unreachable IPv6 first."""
    global _orig_getaddrinfo, _ipv4_dns_patch_applied
    if _ipv4_dns_patch_applied or not enabled:
        return
    raw = database_url
    for prefix in (
        "postgresql+asyncpg://",
        "postgres+asyncpg://",
        "postgresql://",
        "postgres://",
    ):
        if raw.startswith(prefix):
            raw = "postgresql://" + raw.split("://", 1)[1]
            break
    try:
        host = (urlparse(raw).hostname or "").lower()
    except Exception:
        return
    if not host or not _SUPABASE_DIRECT_DB_HOST.match(host):
        return

    _orig_getaddrinfo = socket.getaddrinfo

    def getaddrinfo_ipv4_first(node, port, family=0, type=0, proto=0, flags=0):
        assert _orig_getaddrinfo is not None
        if family == 0 and not _is_local_dns_node(node):
            try:
                return _orig_getaddrinfo(node, port, socket.AF_INET, type, proto, flags)
            except OSError:
                pass
        return _orig_getaddrinfo(node, port, family, type, proto, flags)

    socket.getaddrinfo = getaddrinfo_ipv4_first  # type: ignore[method-assign, assignment]
    _ipv4_dns_patch_applied = True


_maybe_patch_ipv4_first_dns(settings.database_url, settings.database_ipv4_first)


def _asyncpg_connect_args(database_url: str, ssl_mode: str) -> dict:
    """Local Postgres usually has no SSL; managed providers need TLS."""
    mode = (ssl_mode or "auto").strip().lower()
    if mode in ("0", "false", "disable", "off"):
        return {}
    if mode in ("1", "true", "require", "on"):
        # asyncpg + managed Postgres (Supabase/Railway) are most reliable with boolean SSL
        return {"ssl": True}
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
    return {"ssl": True}


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
