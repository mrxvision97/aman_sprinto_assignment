"""
Main pipeline orchestrator.
Runs: Parse → Extract → Contradict → Embed → JD Decompose → Score → Synthesize
Each step updates resume.status so the frontend can show live progress.
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.resume import Resume
from app.models.role import Role
from app.models.score import Score, ResumeChunk


async def run_pipeline(
    resume_id: str,
    role_id: str,
    file_bytes: bytes = None,
    reparse: bool = False,
):
    """
    Full async pipeline for one resume. Called as a BackgroundTask.
    reparse=True skips parsing and storage (already done), re-runs extraction + scoring.
    """
    async with async_session() as db:
        try:
            await _run(db, resume_id, role_id, file_bytes, reparse)
        except Exception as e:
            # Mark resume as error — never leave it stuck in processing
            async with async_session() as err_db:
                try:
                    result = await err_db.execute(select(Resume).where(Resume.id == resume_id))
                    resume = result.scalar_one_or_none()
                    if resume:
                        resume.status = "error"
                        resume.error_message = str(e)[:500]
                        await err_db.commit()
                except Exception:
                    pass


async def _run(db: AsyncSession, resume_id: str, role_id: str, file_bytes: bytes, reparse: bool):
    from app.services.parser import parse_resume
    from app.services.extractor import extract_fields
    from app.services.contradiction import check_contradictions
    from app.services.ai_authorship import detect_ai_authorship
    from app.services.embeddings import chunk_resume, embed_chunks
    from app.services.scorer import score_resume
    from app.services.jd_analyzer import get_or_create_jd_decomposition
    from app.services.rag import get_relevant_chunks, count_chunks_for_role
    from app.services.duplicate import compute_identity_fingerprint

    # Load resume and role
    resume_result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = resume_result.scalar_one_or_none()
    if not resume:
        return

    role_result = await db.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        return

    # ─── STEP 1: Parse ────────────────────────────────────────────────────────
    if not reparse and file_bytes:
        resume.status = "parsing"
        await db.commit()

        parsed = await parse_resume(file_bytes, resume.original_filename)
        resume.parsed_text = parsed.get("parsed_text")
        resume.parse_report = parsed.get("parse_report")
        await db.commit()

        if not resume.parsed_text:
            resume.status = "error"
            resume.error_message = "Could not extract text from file. It may be image-only or corrupted."
            await db.commit()
            return

    if not resume.parsed_text:
        resume.status = "error"
        resume.error_message = "No parsed text available"
        await db.commit()
        return

    # ─── STEP 2: Extract ──────────────────────────────────────────────────────
    resume.status = "extracting"
    await db.commit()

    from app.models.role import DEFAULT_EXTRACTION_CONFIG
    extraction_config = role.extraction_config or DEFAULT_EXTRACTION_CONFIG
    extracted = await extract_fields(resume.parsed_text, extraction_config)
    resume.extracted_fields = extracted
    resume.extraction_config_version = role.extraction_config_version or 1

    # Layer 2 duplicate check: identity fingerprint
    name = extracted.get("full_name", {}).get("value") if isinstance(extracted.get("full_name"), dict) else None
    email = extracted.get("email", {}).get("value") if isinstance(extracted.get("email"), dict) else None
    fingerprint = compute_identity_fingerprint(name, email)

    if fingerprint and not reparse:
        fp_result = await db.execute(
            select(Resume).where(
                Resume.role_id == role_id,
                Resume.id != resume.id,
            )
        )
        existing_resumes = fp_result.scalars().all()
        for existing in existing_resumes:
            existing_name = existing.extracted_fields.get("full_name", {}).get("value") if existing.extracted_fields else None
            existing_email = existing.extracted_fields.get("email", {}).get("value") if existing.extracted_fields else None
            if existing_name and existing_email:
                from app.services.duplicate import compute_identity_fingerprint as cfp
                existing_fp = cfp(existing_name, existing_email)
                if existing_fp == fingerprint:
                    resume.status = "duplicate"
                    resume.duplicate_of_id = existing.id
                    await db.commit()
                    return

    # ─── STEP 3: Contradiction detection ─────────────────────────────────────
    contradiction_flags = check_contradictions(extracted)
    resume.contradiction_flags = contradiction_flags

    # ─── STEP 4: AI authorship signal ────────────────────────────────────────
    authorship_signal = await detect_ai_authorship(resume.parsed_text)
    resume.ai_authorship_signal = authorship_signal
    await db.commit()

    # ─── STEP 5: Chunk + embed for RAG ───────────────────────────────────────
    chunks = chunk_resume(resume.parsed_text)
    if chunks:
        # Delete old chunks if reparse
        if reparse:
            old_chunks = await db.execute(
                select(ResumeChunk).where(ResumeChunk.resume_id == resume.id)
            )
            for c in old_chunks.scalars().all():
                await db.delete(c)
            await db.commit()

        embedded_chunks = await embed_chunks(chunks)
        for chunk in embedded_chunks:
            db.add(ResumeChunk(
                resume_id=resume.id,
                role_id=role.id,
                section_type=chunk["section_type"],
                chunk_text=chunk["chunk_text"],
                chunk_index=chunk["chunk_index"],
                embedding=chunk.get("embedding"),
            ))
        await db.commit()

    # ─── STEP 6: JD decomposition (cached) ───────────────────────────────────
    resume.status = "scoring"
    await db.commit()

    jd_decomposed = await get_or_create_jd_decomposition(role, db)

    # ─── STEP 7: RAG context retrieval ───────────────────────────────────────
    rag_context = ""
    chunk_count = await count_chunks_for_role(str(role_id), db)
    if chunk_count >= 5:  # Only use RAG when there's a meaningful corpus
        requirements = []
        if jd_decomposed:
            for req in jd_decomposed.get("must_haves", [])[:3]:
                if isinstance(req, dict):
                    requirements.append(req.get("requirement", ""))
                else:
                    requirements.append(str(req))
        if requirements:
            rag_context = await get_relevant_chunks(str(role_id), requirements, db)

    # ─── STEP 8: Blind mode — strip PII before scoring ───────────────────────
    scoring_fields = extracted.copy()
    if role.blind_mode:
        scoring_fields = _strip_pii(scoring_fields)

    # ─── STEP 9: Score (PE-05 + PE-06 + PE-07) ───────────────────────────────
    score_result = await score_resume(
        extracted_fields=scoring_fields,
        jd_decomposed=jd_decomposed,
        jd_text=role.jd_text,
        rag_context=rag_context,
    )

    # ─── STEP 10: Save score ──────────────────────────────────────────────────
    # Delete existing score if reparse
    if reparse:
        existing_score = await db.execute(
            select(Score).where(Score.resume_id == resume.id, Score.role_id == role.id)
        )
        old_score = existing_score.scalar_one_or_none()
        if old_score:
            await db.delete(old_score)
            await db.commit()

    score = Score(
        resume_id=resume.id,
        role_id=role.id,
        dimensional_scores=score_result["dimensional_scores"],
        overall_score=score_result["overall_score"],
        strengths=score_result["strengths"],
        concerns=score_result["concerns"],
        recruiter_summary=score_result["recruiter_summary"],
        recommendation=score_result["recommendation"],
        suggested_questions=score_result["suggested_questions"],
        confidence=score_result["confidence"],
        raw_scores=score_result["raw_scores"],
        critique=score_result["critique"],
    )
    db.add(score)

    resume.status = "scored"
    await db.commit()


def _strip_pii(fields: dict) -> dict:
    """Remove PII fields before sending to scoring LLM (blind mode)."""
    pii_fields = {"full_name", "email", "phone"}
    return {k: v for k, v in fields.items() if k not in pii_fields}
