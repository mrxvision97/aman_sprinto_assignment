"""Duplicate detection: SHA-256 file hash + identity fingerprint."""
import hashlib
from typing import Optional


def compute_file_hash(file_bytes: bytes) -> str:
    """SHA-256 hash of raw file bytes — Layer 1 duplicate check."""
    return hashlib.sha256(file_bytes).hexdigest()


def compute_identity_fingerprint(name: Optional[str], email: Optional[str]) -> Optional[str]:
    """Layer 2: hash(normalized_name + normalized_email)."""
    if not name and not email:
        return None
    normalized = f"{_normalize(name)}|{_normalize(email)}"
    return hashlib.sha256(normalized.encode()).hexdigest()


def _normalize(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.lower().strip().replace(" ", "")
