import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Numeric, DateTime, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    dimensional_scores = Column(JSONB, nullable=True)
    overall_score = Column(Numeric(3, 1), nullable=True)
    strengths = Column(JSONB, nullable=True)
    concerns = Column(JSONB, nullable=True)
    recruiter_summary = Column(Text, nullable=True)
    recommendation = Column(String(30), nullable=True)
    suggested_questions = Column(JSONB, nullable=True)
    confidence = Column(String(10), nullable=True)
    raw_scores = Column(JSONB, nullable=True)
    critique = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("resume_id", "role_id", name="uq_resume_role_score"),
    )

    resume = relationship("Resume", back_populates="score")


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    section_type = Column(String(50), nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(SmallInteger, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="chunks")
