"""Multi-role comparison: score one resume against multiple JDs."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.role import Role
from app.services.scorer import score_resume
from app.services.jd_analyzer import get_or_create_jd_decomposition


async def score_against_roles(resume, role_ids: list[str], db: AsyncSession) -> list[dict]:
    """Score a resume against multiple roles and return comparison results."""
    results = []

    for role_id in role_ids:
        role_result = await db.execute(select(Role).where(Role.id == role_id))
        role = role_result.scalar_one_or_none()
        if not role:
            continue

        try:
            jd_decomposed = await get_or_create_jd_decomposition(role, db)
            scoring_fields = resume.extracted_fields or {}
            if role.blind_mode:
                pii = {"full_name", "email", "phone"}
                scoring_fields = {k: v for k, v in scoring_fields.items() if k not in pii}

            score = await score_resume(
                extracted_fields=scoring_fields,
                jd_decomposed=jd_decomposed,
                jd_text=role.jd_text,
            )

            results.append({
                "role_id": str(role.id),
                "role_title": role.title,
                "overall_score": score["overall_score"],
                "dimensional_scores": score["dimensional_scores"],
                "recommendation": score["recommendation"],
                "confidence": score["confidence"],
            })
        except Exception as e:
            results.append({
                "role_id": str(role.id),
                "role_title": role.title,
                "overall_score": None,
                "dimensional_scores": [],
                "recommendation": "error",
                "confidence": "low",
                "error": str(e),
            })

    return results
