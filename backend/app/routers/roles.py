from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.role import Role, DEFAULT_EXTRACTION_CONFIG
from app.models.resume import Resume
from app.models.score import Score
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    ExtractionConfigUpdate,
    JDPreviewRequest,
)
from uuid import UUID

router = APIRouter(prefix="/api/roles", tags=["roles"])

@router.post("/analyze-jd-preview")
async def analyze_jd_preview(data: JDPreviewRequest):
    """
    Preview JD quality analysis without creating/updating any role.
    Returns the same `quality_report` shape used by the role-scoped analyzer UI.
    """
    from app.services.jd_analyzer import analyze_jd_quality

    result = await analyze_jd_quality(data.jd_text)
    return result.get("quality_report", {"flags": [], "overall_quality": "fair"})


@router.post("", response_model=RoleResponse)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    # `extraction_config` may arrive as `[]` (or as a list of Pydantic models).
    # We normalize it to JSON-serializable dicts, and fall back to defaults when empty.
    extraction_config = (
        [f.model_dump() for f in data.extraction_config]
        if data.extraction_config
        else DEFAULT_EXTRACTION_CONFIG
    )
    role = Role(
        title=data.title,
        jd_text=data.jd_text,
        blind_mode=data.blind_mode,
        extraction_config=extraction_config,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return await _build_role_response(role, db)


@router.get("", response_model=list[RoleListResponse])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).where(Role.status != "archived").order_by(Role.created_at.desc()))
    roles = result.scalars().all()
    return [await _build_role_response(r, db) for r in roles]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: UUID, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    return await _build_role_response(role, db)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: UUID, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    if data.title is not None:
        role.title = data.title
    if data.jd_text is not None:
        role.jd_text = data.jd_text
        role.jd_decomposed = None  # invalidate cached decomposition
        role.jd_quality_report = None
    if data.blind_mode is not None:
        role.blind_mode = data.blind_mode
    if data.status is not None:
        role.status = data.status
    await db.commit()
    await db.refresh(role)
    return await _build_role_response(role, db)


@router.delete("/{role_id}")
async def delete_role(role_id: UUID, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    await db.delete(role)
    await db.commit()
    return {"message": "Role deleted"}


@router.post("/{role_id}/analyze-jd")
async def analyze_jd(role_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    from app.services.jd_analyzer import analyze_jd_quality
    result = await analyze_jd_quality(role.jd_text)
    role.jd_decomposed = result.get("decomposed")
    role.jd_quality_report = result.get("quality_report")
    await db.commit()
    return role.jd_quality_report or {}


@router.get("/{role_id}/config")
async def get_config(role_id: UUID, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    return {"extraction_config": role.extraction_config, "version": role.extraction_config_version}


@router.put("/{role_id}/config")
async def update_config(role_id: UUID, data: ExtractionConfigUpdate, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    role.extraction_config = [f.model_dump() for f in data.extraction_config]
    role.extraction_config_version = (role.extraction_config_version or 1) + 1
    await db.commit()
    return {"message": "Config updated", "version": role.extraction_config_version}


@router.post("/{role_id}/batch-reparse")
async def batch_reparse(role_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    role = await _get_or_404(role_id, db)
    result = await db.execute(
        select(Resume).where(Resume.role_id == role_id, Resume.status == "scored")
    )
    resumes = result.scalars().all()

    from app.services.pipeline import run_pipeline
    for resume in resumes:
        resume.status = "extracting"
        background_tasks.add_task(run_pipeline, str(resume.id), str(role_id), reparse=True)

    await db.commit()
    return {"message": f"Re-parsing {len(resumes)} resumes", "count": len(resumes)}


async def _get_or_404(role_id: UUID, db: AsyncSession) -> Role:
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


async def _build_role_response(role: Role, db: AsyncSession) -> dict:
    resume_count_result = await db.execute(
        select(func.count(Resume.id)).where(Resume.role_id == role.id)
    )
    resume_count = resume_count_result.scalar() or 0

    scored_result = await db.execute(
        select(func.count(Resume.id)).where(Resume.role_id == role.id, Resume.status == "scored")
    )
    scored_count = scored_result.scalar() or 0

    avg_result = await db.execute(
        select(func.avg(Score.overall_score)).where(Score.role_id == role.id)
    )
    avg_score = avg_result.scalar()

    return {
        "id": role.id,
        "title": role.title,
        "jd_text": role.jd_text,
        "jd_decomposed": role.jd_decomposed,
        "jd_quality_report": role.jd_quality_report,
        "extraction_config": role.extraction_config or [],
        "extraction_config_version": role.extraction_config_version or 1,
        "blind_mode": role.blind_mode,
        "status": role.status,
        "created_at": role.created_at,
        "resume_count": resume_count,
        "scored_count": scored_count,
        "avg_score": float(avg_score) if avg_score else None,
    }
