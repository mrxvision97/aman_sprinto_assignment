from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ExtractionField(BaseModel):
    field: str
    label: str
    type: str  # text, number, list
    enabled: bool = True
    description: str = ""


class RoleCreate(BaseModel):
    title: str
    jd_text: str
    extraction_config: Optional[list[ExtractionField]] = None
    blind_mode: bool = True


class RoleUpdate(BaseModel):
    title: Optional[str] = None
    jd_text: Optional[str] = None
    blind_mode: Optional[bool] = None
    status: Optional[str] = None


class RoleResponse(BaseModel):
    id: UUID
    title: str
    jd_text: str
    jd_decomposed: Optional[dict] = None
    jd_quality_report: Optional[dict] = None
    extraction_config: list[dict]
    extraction_config_version: int
    blind_mode: bool
    status: str
    created_at: datetime
    resume_count: int = 0
    scored_count: int = 0
    avg_score: Optional[float] = None

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    id: UUID
    title: str
    status: str
    blind_mode: bool
    created_at: datetime
    resume_count: int = 0
    scored_count: int = 0
    avg_score: Optional[float] = None

    class Config:
        from_attributes = True


class ExtractionConfigUpdate(BaseModel):
    extraction_config: list[ExtractionField]


class JDPreviewRequest(BaseModel):
    jd_text: str
