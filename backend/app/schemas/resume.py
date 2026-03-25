from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ResumeResponse(BaseModel):
    id: UUID
    role_id: UUID
    original_filename: str
    file_hash: str
    parsed_text: Optional[str] = None
    parse_report: Optional[dict] = None
    extracted_fields: Optional[dict] = None
    extraction_config_version: int
    contradiction_flags: Optional[list] = None
    ai_authorship_signal: str
    duplicate_of_id: Optional[UUID] = None
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    score: Optional["ScoreSummary"] = None

    class Config:
        from_attributes = True


class ScoreSummary(BaseModel):
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    confidence: Optional[str] = None
    recruiter_summary: Optional[str] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    id: UUID
    status: str
    duplicate: bool = False
    duplicate_of_id: Optional[UUID] = None
    message: str
