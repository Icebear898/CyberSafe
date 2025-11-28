"""
Mental health support and reporting endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.schemas.support import MentalHealthRequest, MentalHealthResponse
from app.services.ai_detection import ai_detection_service
from app.models.user import User
from app.models.report import Report, ReportStatus

router = APIRouter()


class ReportCreate(BaseModel):
    reported_user_id: int
    reason: str
    description: str
    message_id: int | None = None


@router.post("/chat", response_model=MentalHealthResponse)
async def mental_health_chat(
    payload: MentalHealthRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate an empathetic response from the mental health assistant.
    """
    reply = await ai_detection_service.generate_support_response(
        message=payload.message,
        history=[msg.dict() for msg in payload.history or []],
    )
    return MentalHealthResponse(reply=reply)


@router.post("/report")
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user-initiated report"""
    # Verify reported user exists
    reported_user = db.query(User).filter(User.id == report_data.reported_user_id).first()
    if not reported_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reported user not found"
        )
    
    # Create report
    new_report = Report(
        reporter_id=current_user.id,
        reported_user_id=report_data.reported_user_id,
        report_type=report_data.reason,
        description=report_data.description,
        message_id=report_data.message_id,
        status=ReportStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return {
        "message": "Report submitted successfully",
        "report_id": new_report.id
    }
