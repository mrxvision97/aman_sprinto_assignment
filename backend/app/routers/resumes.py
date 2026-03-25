from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.resume import Resume
from app.models.role import Role
from app.models.score import Score
from app.schemas.resume import UploadResponse
from app.schemas.score import MultiRoleRequest
from app.services.duplicate import compute_file_hash
from app.services.parser import parse_resume
from app.services.storage import upload_file
import uuid
from uuid import UUID

router = APIRouter(prefix="/api", tags=["resumes"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/roles/{role_id}/resumes", response_model=UploadResponse)
async def upload_resume(
    role_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    # Validate role exists
    role_result = await db.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Validate file type
    filename = file.filename or "resume"
    ext = filename.lower().split(".")[-1]
    if ext not in ("pdf", "docx", "doc"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    # Layer 1: file hash duplicate check
    file_hash = compute_file_hash(file_bytes)
    existing_result = await db.execute(
        select(Resume).where(Resume.role_id == role_id, Resume.file_hash == file_hash)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        return UploadResponse(
            id=existing.id,
            status="duplicate",
            duplicate=True,
            duplicate_of_id=existing.id,
            message=f"This exact file was already uploaded as '{existing.original_filename}'",
        )

    # Create resume record
    resume_id = uuid.uuid4()
    resume = Resume(
        id=resume_id,
        role_id=role_id,
        original_filename=filename,
        file_hash=file_hash,
        status="parsing",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # Upload to Supabase (best-effort)
    try:
        storage_path = upload_file(str(role_id), str(resume_id), filename, file_bytes)
        resume.storage_path = storage_path
        await db.commit()
    except Exception:
        pass  # Continue even if storage fails

    # Start background pipeline
    from app.services.pipeline import run_pipeline
    background_tasks.add_task(run_pipeline, str(resume_id), str(role_id), file_bytes=file_bytes)

    return UploadResponse(
        id=resume.id,
        status="processing",
        duplicate=False,
        message="Resume uploaded and processing started",
    )


@router.get("/roles/{role_id}/resumes")
async def list_resumes(role_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.score))
        .where(Resume.role_id == role_id)
        .order_by(Resume.uploaded_at.desc())
    )
    resumes = result.scalars().all()
    return [_resume_to_dict(r) for r in resumes]


@router.get("/resumes/{resume_id}")
async def get_resume(resume_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume).options(selectinload(Resume.score)).where(Resume.id == resume_id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _resume_to_dict(resume)


@router.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.storage_path:
        from app.services.storage import delete_file
        delete_file(resume.storage_path)
    await db.delete(resume)
    await db.commit()
    return {"message": "Resume deleted"}


@router.post("/resumes/{resume_id}/multi-role")
async def multi_role_score(resume_id: UUID, data: MultiRoleRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.extracted_fields or not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume must be fully processed before multi-role comparison")

    from app.services.multi_role import score_against_roles
    results = await score_against_roles(resume, [str(rid) for rid in data.role_ids], db)
    return results


def _resume_to_dict(resume: Resume) -> dict:
    score = resume.score
    return {
        "id": str(resume.id),
        "role_id": str(resume.role_id),
        "original_filename": resume.original_filename,
        "file_hash": resume.file_hash,
        "parsed_text": resume.parsed_text,
        "parse_report": resume.parse_report,
        "extracted_fields": resume.extracted_fields,
        "extraction_config_version": resume.extraction_config_version,
        "contradiction_flags": resume.contradiction_flags,
        "ai_authorship_signal": resume.ai_authorship_signal,
        "duplicate_of_id": str(resume.duplicate_of_id) if resume.duplicate_of_id else None,
        "status": resume.status,
        "error_message": resume.error_message,
        "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
        "score": {
            "overall_score": float(score.overall_score) if score and score.overall_score else None,
            "recommendation": score.recommendation if score else None,
            "confidence": score.confidence if score else None,
            "recruiter_summary": score.recruiter_summary if score else None,
            "dimensional_scores": score.dimensional_scores if score else None,
            "strengths": score.strengths if score else None,
            "concerns": score.concerns if score else None,
            "suggested_questions": score.suggested_questions if score else None,
            "raw_scores": score.raw_scores if score else None,
            "critique": score.critique if score else None,
        } if score else None,
    }
