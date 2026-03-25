"""RAG: Query resume chunks by JD requirement using pgvector similarity search."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.score import ResumeChunk
from app.services.gemini import embed_text


async def get_relevant_chunks(
    role_id: str,
    jd_requirements: list[str],
    db: AsyncSession,
    top_k: int = 3,
) -> str:
    """
    For each JD requirement, find the most relevant resume chunks via vector similarity.
    Returns a formatted string of relevant passages for inclusion in the scoring prompt.
    """
    if not jd_requirements:
        return ""

    context_parts = []
    for requirement in jd_requirements[:4]:  # Limit to 4 requirements for token budget
        try:
            query_embedding = await embed_text(f"Evidence of: {requirement}")
            embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

            async with db.begin_nested():
                result = await db.execute(
                    text(f"""
                        SELECT chunk_text, section_type,
                               1 - (embedding <=> '{embedding_str}'::vector) AS similarity
                        FROM resume_chunks
                        WHERE role_id = :role_id
                          AND embedding IS NOT NULL
                        ORDER BY embedding <=> '{embedding_str}'::vector
                        LIMIT :top_k
                    """),
                    {"role_id": role_id, "top_k": top_k},
                )
                rows = result.fetchall()
            if rows:
                best = rows[0]
                if best.similarity > 0.5:  # Only include if reasonably relevant
                    context_parts.append(
                        f"Requirement: {requirement}\n"
                        f"Most relevant passage ({best.section_type}): {best.chunk_text[:300]}"
                    )
        except Exception:
            continue  # RAG is best-effort — don't block scoring

    return "\n\n".join(context_parts)


async def count_chunks_for_role(role_id: str, db: AsyncSession) -> int:
    """Count how many chunks exist for a role (to decide if RAG is worth it)."""
    try:
        result = await db.execute(
            select(ResumeChunk).where(ResumeChunk.role_id == role_id)
        )
        return len(result.scalars().all())
    except Exception:
        return 0
