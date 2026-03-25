import ssl as _ssl
import socket
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Hosts that never need the IPv4-first DNS patch (local dev).
_LOCAL_DNS_NAMES = frozenset({"localhost", "127.0.0.1", "::1", "postgres", "db"})
_orig_getaddrinfo = None
_ipv4_dns_patch_applied = False


def _is_local_dns_node(node: object) -> bool:
    if node is None:
        return True
    h = str(node).lower().rstrip(".")
    if h in _LOCAL_DNS_NAMES:
        return True
    return h.endswith(".local")


def _maybe_patch_ipv4_first_dns(database_url: str, enabled: bool) -> None:
    """Prefer IPv4 (A records) for ALL remote hosts so asyncpg/uvloop do not try unreachable IPv6 first.

    Railway and many container platforms have IPv4-only egress. When DNS returns
    AAAA records first, asyncpg immediately fails with 'Network is unreachable'.
    """
    global _orig_getaddrinfo, _ipv4_dns_patch_applied
    if _ipv4_dns_patch_applied or not enabled:
        return

    # Only patch if the DB host is remote (not localhost/docker).
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
    if not host or _is_local_dns_node(host):
        return

    _orig_getaddrinfo = socket.getaddrinfo

    def getaddrinfo_ipv4_first(node, port, family=0, type=0, proto=0, flags=0):
        if family == 0 and not _is_local_dns_node(node):
            try:
                return _orig_getaddrinfo(node, port, socket.AF_INET, type, proto, flags)
            except OSError:
                pass
        return _orig_getaddrinfo(node, port, family, type, proto, flags)

    socket.getaddrinfo = getaddrinfo_ipv4_first  # type: ignore[method-assign, assignment]
    _ipv4_dns_patch_applied = True
    logger.info("IPv4-first DNS patch applied for remote database host: %s", host)


_maybe_patch_ipv4_first_dns(settings.database_url, settings.database_ipv4_first)


def _parse_db_host(database_url: str) -> str:
    raw = database_url
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if raw.startswith(prefix):
            raw = "postgresql://" + raw.split("://", 1)[1]
            break
    try:
        return (urlparse(raw).hostname or "").lower()
    except Exception:
        return ""


def _parse_db_port(database_url: str) -> int:
    raw = database_url
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if raw.startswith(prefix):
            raw = "postgresql://" + raw.split("://", 1)[1]
            break
    try:
        return urlparse(raw).port or 5432
    except Exception:
        return 5432


def _is_pooler_connection(database_url: str) -> bool:
    """Detect Supabase connection pooler (Supavisor) by host/port."""
    host = _parse_db_host(database_url)
    port = _parse_db_port(database_url)
    return "pooler.supabase.com" in host or port == 6543


def _disable_sqlalchemy_stmt_cache(database_url: str) -> str:
    """Append prepared_statement_cache_size=0 to the URL for SQLAlchemy's asyncpg dialect."""
    if "prepared_statement_cache_size" in database_url:
        return database_url
    separator = "&" if "?" in database_url else "?"
    return database_url + separator + "prepared_statement_cache_size=0"


def _make_ssl_context() -> _ssl.SSLContext:
    """Create an SSL context that encrypts traffic but does not verify certificates.

    Supabase pooler (Supavisor) and many managed Postgres providers use certificates
    that Python's default trust store doesn't recognise, causing CERTIFICATE_VERIFY_FAILED.
    """
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    return ctx


def _asyncpg_connect_args(database_url: str, ssl_mode: str) -> dict:
    """Local Postgres usually has no SSL; managed providers need TLS."""
    args: dict = {}
    host = _parse_db_host(database_url)

    # SSL handling — use a permissive context to avoid CERTIFICATE_VERIFY_FAILED
    mode = (ssl_mode or "auto").strip().lower()
    need_ssl = False
    if mode in ("0", "false", "disable", "off"):
        pass
    elif mode in ("1", "true", "require", "on"):
        need_ssl = True
    elif host not in ("localhost", "127.0.0.1", "::1", "postgres", "db") and not host.endswith(".local"):
        need_ssl = True

    if need_ssl:
        args["ssl"] = _make_ssl_context()

    # Pooler connections (PgBouncer/Supavisor) do not support prepared statements
    if _is_pooler_connection(database_url):
        args["statement_cache_size"] = 0
        logger.info("Pooler connection detected — disabled prepared statement cache")

    return args


_db_url = settings.database_url
if _is_pooler_connection(_db_url):
    _db_url = _disable_sqlalchemy_stmt_cache(_db_url)

engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args=_asyncpg_connect_args(settings.database_url, settings.database_ssl),
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    try:
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
    except OSError as exc:
        from fastapi import HTTPException
        logger.error("Database connection failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database is temporarily unavailable. Please retry shortly.")


async def init_db(retries: int = 10, delay: float = 5.0):
    import asyncio
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

                from app.models import role, resume, score  # noqa: F401
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully on attempt %d", attempt)
            return
        except Exception as exc:
            logger.warning("Database init attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                raise
