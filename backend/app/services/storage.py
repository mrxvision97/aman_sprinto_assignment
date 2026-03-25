"""Supabase Storage integration for resume files."""
import io
from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()
BUCKET = "resumes"

_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None and settings.supabase_url and settings.supabase_key:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def upload_file(role_id: str, resume_id: str, filename: str, file_bytes: bytes) -> str:
    """Upload file to Supabase Storage and return the storage path."""
    client = get_client()
    if not client:
        return f"local/{role_id}/{resume_id}/{filename}"

    path = f"{role_id}/{resume_id}/{filename}"
    client.storage.from_(BUCKET).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": _get_content_type(filename)},
    )
    return path


def get_public_url(storage_path: str) -> str:
    """Get public URL for a stored file."""
    client = get_client()
    if not client:
        return ""
    return client.storage.from_(BUCKET).get_public_url(storage_path)


def delete_file(storage_path: str) -> None:
    """Delete a file from Supabase Storage."""
    client = get_client()
    if not client:
        return
    try:
        client.storage.from_(BUCKET).remove([storage_path])
    except Exception:
        pass


def _get_content_type(filename: str) -> str:
    ext = filename.lower().split(".")[-1]
    return {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(ext, "application/octet-stream")
