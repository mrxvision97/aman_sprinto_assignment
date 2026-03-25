import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

DEFAULT_EXTRACTION_CONFIG = [
    {"field": "full_name", "label": "Full Name", "type": "text", "enabled": True, "description": "Candidate full name"},
    {"field": "email", "label": "Email", "type": "text", "enabled": True, "description": "Contact email address"},
    {"field": "phone", "label": "Phone", "type": "text", "enabled": True, "description": "Phone number"},
    {"field": "current_title", "label": "Current Job Title", "type": "text", "enabled": True, "description": "Most recent job title"},
    {"field": "total_experience_years", "label": "Years of Experience", "type": "number", "enabled": True, "description": "Total years of professional experience"},
    {"field": "skills", "label": "Key Skills", "type": "list", "enabled": True, "description": "Technical and professional skills"},
    {"field": "education", "label": "Education", "type": "text", "enabled": True, "description": "Degrees and institutions"},
    {"field": "summary", "label": "Professional Summary", "type": "text", "enabled": True, "description": "Brief career summary"},
]


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    jd_text = Column(Text, nullable=False)
    jd_decomposed = Column(JSONB, nullable=True)
    jd_quality_report = Column(JSONB, nullable=True)
    extraction_config = Column(JSONB, nullable=False, default=DEFAULT_EXTRACTION_CONFIG)
    extraction_config_version = Column(Integer, default=1)
    blind_mode = Column(Boolean, default=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    resumes = relationship("Resume", back_populates="role", cascade="all, delete-orphan")
