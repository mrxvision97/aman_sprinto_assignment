from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Sprinto AI Resume Screener",
    description="AI-powered resume screening and ranking against job descriptions",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
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
    return {"status": "ok", "service": "sprinto-resume-screener"}


@app.post("/api/seed")
async def seed_data():
    """Seed sample data for demo purposes."""
    from app.seed import seed
    await seed()
    return {"message": "Sample data seeded successfully"}
