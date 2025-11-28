"""
Incident model for tracking abusive behavior
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.PENDING)
    
    # Details
    detected_content = Column(Text, nullable=False)
    content_filtered = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    evidence_path = Column(String, nullable=True)
    
    # AI Analysis
    ai_analysis = Column(Text, nullable=True)
    detection_model = Column(String, nullable=True)
    confidence_score = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="incidents")

