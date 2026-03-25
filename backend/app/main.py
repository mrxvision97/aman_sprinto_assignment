from contextlib import asynccontextmanager
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db


logger = logging.getLogger(__name__)


async def _initialize_database(app: FastAPI):
    try:
        await init_db()
        app.state.db_ready = True
    except Exception:
        # Keep the API process alive so platform health checks can pass and retries can happen.
        logger.exception("Database initialization failed during startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_ready = False
    app.state.db_init_task = asyncio.create_task(_initialize_database(app))
    yield


app = FastAPI(
    title="Sprinto AI Resume Screener",
    description="AI-powered resume screening and ranking against job descriptions",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

_dev = settings.environment == "development"
_origins = [o.strip() for o in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r".*" if _dev else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routers import roles, resumes  # noqa: E402
app.include_router(roles.router)
app.include_router(resumes.router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "sprinto-resume-screener",
        "db_ready": bool(getattr(app.state, "db_ready", False)),
    }


@app.post("/api/seed")
async def seed_data():
    """
    Reset demo data: removes all roles (and resumes/scores/chunks via cascade),
    then inserts the curated multi-role showcase dataset.
    """
    from app.seed import seed
    await seed()
    return {
        "message": "Demo dataset loaded successfully.",
        "note": "All previous roles and candidates were replaced.",
    }
