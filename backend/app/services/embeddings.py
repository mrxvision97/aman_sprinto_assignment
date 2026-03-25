"""
Resume section chunking and embedding for RAG.
Splits parsed resume text into semantic sections, embeds each with Gemini text-embedding-004.
"""
import re
from app.services.gemini import embed_text

SECTION_HEADERS = re.compile(
    r"\n(EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|EDUCATION|SKILLS|TECHNICAL SKILLS|"
    r"PROJECTS|CERTIFICATIONS|SUMMARY|OBJECTIVE|PROFILE|ACHIEVEMENTS|PUBLICATIONS)\n",
    re.IGNORECASE,
)


def chunk_resume(parsed_text: str) -> list[dict]:
    """Split resume into sections and return chunks with section type."""
    if not parsed_text:
        return []

    # Split on section headers
    parts = SECTION_HEADERS.split(parsed_text)
    chunks = []
    i = 0
    chunk_index = 0

    if parts:
        # First part is usually contact/header info
        first = parts[0].strip()
        if first:
            chunks.append({
                "section_type": "contact",
                "chunk_text": first[:1000],
                "chunk_index": chunk_index,
            })
            chunk_index += 1
        i = 1

    # Process header-content pairs
    while i < len(parts) - 1:
        section_name = parts[i].strip().upper()
        content = parts[i + 1].strip()

        section_type = _map_section(section_name)

        if content:
            # Trim to max 1500 chars per chunk for embedding quality
            chunks.append({
                "section_type": section_type,
                "chunk_text": content[:1500],
                "chunk_index": chunk_index,
            })
            chunk_index += 1
        i += 2

    # If no sections detected, use whole text
    if not chunks and parsed_text:
        chunks.append({
            "section_type": "full",
            "chunk_text": parsed_text[:2000],
            "chunk_index": 0,
        })

    return chunks


async def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add embeddings to each chunk."""
    embedded = []
    for chunk in chunks:
        try:
            vector = await embed_text(chunk["chunk_text"])
            embedded.append({**chunk, "embedding": vector})
        except Exception:
            embedded.append({**chunk, "embedding": None})
    return embedded


def _map_section(header: str) -> str:
    mapping = {
        "EXPERIENCE": "experience",
        "WORK EXPERIENCE": "experience",
        "EMPLOYMENT": "experience",
        "EDUCATION": "education",
        "SKILLS": "skills",
        "TECHNICAL SKILLS": "skills",
        "PROJECTS": "projects",
        "CERTIFICATIONS": "certifications",
        "SUMMARY": "summary",
        "OBJECTIVE": "summary",
        "PROFILE": "summary",
        "ACHIEVEMENTS": "achievements",
    }
    return mapping.get(header.upper(), "other")
