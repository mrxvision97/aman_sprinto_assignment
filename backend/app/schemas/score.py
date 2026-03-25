from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DimensionScore(BaseModel):
    dimension: str
    score: float
    evidence: list[str]
    gaps: list[str] = []


class Strength(BaseModel):
    point: str
    evidence: str


class Concern(BaseModel):
    point: str
    evidence: str
    suggested_question: str


class SuggestedQuestion(BaseModel):
    question: str
    addresses: str


class ScoreResponse(BaseModel):
    id: UUID
    resume_id: UUID
    role_id: UUID
    dimensional_scores: Optional[list[dict]] = None
    overall_score: Optional[float] = None
    strengths: Optional[list[dict]] = None
    concerns: Optional[list[dict]] = None
    recruiter_summary: Optional[str] = None
    recommendation: Optional[str] = None
    suggested_questions: Optional[list[dict]] = None
    confidence: Optional[str] = None
    raw_scores: Optional[dict] = None
    critique: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MultiRoleRequest(BaseModel):
    role_ids: list[UUID]


class MultiRoleScoreResult(BaseModel):
    role_id: UUID
    role_title: str
    overall_score: Optional[float] = None
    dimensional_scores: Optional[list[dict]] = None
    recommendation: Optional[str] = None
