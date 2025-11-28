"""
Report model for user-generated reports
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class ReportType(str, enum.Enum):
    HARASSMENT = "harassment"
    CYBERBULLYING = "cyberbullying"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM = "spam"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    report_type = Column(SQLEnum(ReportType), nullable=False)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    description = Column(Text, nullable=False)
    evidence_paths = Column(Text, nullable=True)  # JSON array of paths
    
    is_urgent = Column(Boolean, default=False)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    reporter = relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reports",
    )
    reported_user = relationship(
        "User",
        foreign_keys=[reported_user_id],
        back_populates="reports_received",
    )

