import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    storage_path = Column(String(512), nullable=True)
    parsed_text = Column(Text, nullable=True)
    parse_report = Column(JSONB, nullable=True)
    extracted_fields = Column(JSONB, nullable=True)
    extraction_config_version = Column(Integer, default=1)
    contradiction_flags = Column(JSONB, nullable=True)
    ai_authorship_signal = Column(String(20), default="none")
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    status = Column(String(30), default="pending")
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("role_id", "file_hash", name="uq_role_file_hash"),
    )

    role = relationship("Role", back_populates="resumes")
    score = relationship("Score", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    chunks = relationship("ResumeChunk", back_populates="resume", cascade="all, delete-orphan")
