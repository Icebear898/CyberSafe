"""
Admin dashboard and management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_admin_user
from app.models.user import User
from app.models.incident import Incident, IncidentStatus
from app.models.report import Report, ReportStatus
from app.models.message import Message
from app.services.evidence_logger import evidence_logger

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    blocked_users = db.query(User).filter(User.is_blocked == True).count()
    red_tagged_users = db.query(User).filter(User.has_red_tag == True).count()
    
    total_incidents = db.query(Incident).count()
    pending_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.PENDING).count()
    high_severity_incidents = db.query(Incident).filter(Incident.severity == "high").count()
    
    total_reports = db.query(Report).count()
    pending_reports = db.query(Report).filter(Report.status == ReportStatus.PENDING).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "blocked": blocked_users,
            "red_tagged": red_tagged_users
        },
        "incidents": {
            "total": total_incidents,
            "pending": pending_incidents,
            "high_severity": high_severity_incidents
        },
        "reports": {
            "total": total_reports,
            "pending": pending_reports
        }
    }


@router.get("/incidents", response_model=List[dict])
async def get_all_incidents(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all incidents with filters"""
    query = db.query(Incident)
    
    if status_filter:
        query = query.filter(Incident.status == IncidentStatus(status_filter))
    
    if severity_filter:
        query = query.filter(Incident.severity == severity_filter)
    
    incidents = query.order_by(Incident.created_at.desc()).limit(100).all()
    
    result = []
    for incident in incidents:
        user = db.query(User).filter(User.id == incident.user_id).first()
        result.append({
            "id": incident.id,
            "user": {
                "id": user.id if user else None,
                "username": user.username if user else "Unknown",
                "has_red_tag": user.has_red_tag if user else False
            },
            "severity": incident.severity,
            "status": incident.status,
            "detected_content": incident.detected_content,
            "ai_analysis": incident.ai_analysis,
            "screenshot_path": incident.screenshot_path,
            "created_at": incident.created_at.isoformat()
        })
    
    return result


@router.put("/incidents/{incident_id}")
async def update_incident_status(
    incident_id: int,
    status: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update incident status"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    incident.status = IncidentStatus(status)
    incident.reviewed_at = datetime.utcnow()
    
    if status == "resolved":
        incident.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(incident)
    
    return {"message": "Incident status updated", "incident": incident}


@router.get("/reports", response_model=List[dict])
async def get_all_reports(
    status_filter: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all reports"""
    query = db.query(Report)
    
    if status_filter:
        query = query.filter(Report.status == ReportStatus(status_filter))
    
    reports = query.order_by(Report.created_at.desc()).limit(100).all()
    
    result = []
    for report in reports:
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        reported_user = db.query(User).filter(User.id == report.reported_user_id).first() if report.reported_user_id else None
        
        result.append({
            "id": report.id,
            "reporter": {
                "id": reporter.id if reporter else None,
                "username": reporter.username if reporter else "Unknown"
            },
            "reported_user": {
                "id": reported_user.id if reported_user else None,
                "username": reported_user.username if reported_user else "Unknown"
            } if reported_user else None,
            "report_type": report.report_type,
            "status": report.status,
            "description": report.description,
            "is_urgent": report.is_urgent,
            "created_at": report.created_at.isoformat()
        })
    
    return result


@router.put("/reports/{report_id}")
async def update_report_status(
    report_id: int,
    status: str,
    admin_notes: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update report status"""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    report.status = ReportStatus(status)
    report.reviewed_at = datetime.utcnow()
    
    if admin_notes:
        report.admin_notes = admin_notes
    
    if status == "resolved":
        report.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(report)
    
    return {"message": "Report status updated", "report": report}


@router.get("/users", response_model=List[dict])
async def get_all_users(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        incident_count = db.query(Incident).filter(Incident.user_id == user.id).count()
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "has_red_tag": user.has_red_tag,
            "warning_count": user.warning_count,
            "is_blocked": user.is_blocked,
            "is_active": user.is_active,
            "incident_count": incident_count,
            "created_at": user.created_at.isoformat()
        })
    
    return result


class UpdateTagRequest(BaseModel):
    has_red_tag: bool


@router.put("/users/{user_id}/tag")
async def update_user_tag(
    user_id: int,
    request_data: UpdateTagRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user red tag status"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.has_red_tag = request_data.has_red_tag
    db.commit()
    db.refresh(user)
    
    return {"message": "User tag updated", "user": {"id": user.id, "has_red_tag": user.has_red_tag}}


class UpdateBlockRequest(BaseModel):
    is_blocked: bool


@router.put("/users/{user_id}/block")
async def block_unblock_user(
    user_id: int,
    request_data: UpdateBlockRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Block or unblock a user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_blocked = request_data.is_blocked
    db.commit()
    db.refresh(user)
    
    return {"message": f"User {'blocked' if request_data.is_blocked else 'unblocked'}", "user": {"id": user.id, "is_blocked": user.is_blocked}}


@router.get("/reports/generate")
async def generate_report(
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate evidence report"""
    report_data = evidence_logger.generate_report(user_id, start_date, end_date)
    return report_data


@router.get("/incidents/{incident_id}/details")
async def get_incident_details(
    incident_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed incident information including screenshots and user context"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Get user who triggered the incident
    user = db.query(User).filter(User.id == incident.user_id).first()
    
    # Get the message that triggered the incident
    message = db.query(Message).filter(Message.id == incident.message_id).first() if incident.message_id else None
    
    # Get sender and receiver info
    sender = None
    receiver = None
    if message:
        sender = db.query(User).filter(User.id == message.sender_id).first()
        receiver = db.query(User).filter(User.id == message.receiver_id).first()
    
    # Get conversation context (5 messages before and after)
    conversation_context = []
    if message:
        context_messages = db.query(Message).filter(
            ((Message.sender_id == message.sender_id) & (Message.receiver_id == message.receiver_id)) |
            ((Message.sender_id == message.receiver_id) & (Message.receiver_id == message.sender_id))
        ).order_by(Message.created_at.desc()).limit(11).all()
        
        for msg in reversed(context_messages):
            msg_sender = db.query(User).filter(User.id == msg.sender_id).first()
            conversation_context.append({
                "id": msg.id,
                "sender": {
                    "id": msg_sender.id if msg_sender else None,
                    "username": msg_sender.username if msg_sender else "Unknown",
                    "avatar_url": msg_sender.avatar_url if msg_sender else None
                },
                "content": msg.content,
                "content_filtered": msg.content_filtered,
                "is_flagged": msg.is_flagged,
                "created_at": msg.created_at.isoformat(),
                "is_incident_message": msg.id == message.id
            })
    
    return {
        "id": incident.id,
        "severity": incident.severity,
        "status": incident.status,
        "detected_content": incident.detected_content,
        "ai_analysis": incident.ai_analysis,
        "screenshot_path": incident.screenshot_path,
        "created_at": incident.created_at.isoformat(),
        "reviewed_at": incident.reviewed_at.isoformat() if incident.reviewed_at else None,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "user": {
            "id": user.id if user else None,
            "username": user.username if user else "Unknown",
            "email": user.email if user else None,
            "full_name": user.full_name if user else None,
            "avatar_url": user.avatar_url if user else None,
            "has_red_tag": user.has_red_tag if user else False,
            "warning_count": user.warning_count if user else 0,
            "is_blocked": user.is_blocked if user else False
        },
        "message": {
            "id": message.id if message else None,
            "content": message.content if message else None,
            "content_filtered": message.content_filtered if message else None,
            "message_type": message.message_type if message else None,
            "severity_score": message.severity_score if message else None,
            "created_at": message.created_at.isoformat() if message else None
        } if message else None,
        "sender": {
            "id": sender.id if sender else None,
            "username": sender.username if sender else "Unknown",
            "email": sender.email if sender else None,
            "avatar_url": sender.avatar_url if sender else None,
            "has_red_tag": sender.has_red_tag if sender else False
        } if sender else None,
        "receiver": {
            "id": receiver.id if receiver else None,
            "username": receiver.username if receiver else "Unknown",
            "email": receiver.email if receiver else None,
            "avatar_url": receiver.avatar_url if receiver else None,
            "has_red_tag": receiver.has_red_tag if receiver else False
        } if receiver else None,
        "conversation_context": conversation_context
    }


@router.get("/analytics")
async def get_analytics(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get analytics data for dashboard charts"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Get incidents by severity
    severity_stats = db.query(
        Incident.severity,
        func.count(Incident.id).label('count')
    ).group_by(Incident.severity).all()
    
    # Get incidents over last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_incidents = db.query(
        func.date(Incident.created_at).label('date'),
        func.count(Incident.id).label('count')
    ).filter(Incident.created_at >= seven_days_ago).group_by(
        func.date(Incident.created_at)
    ).all()
    
    # Get top violators
    top_violators = db.query(
        User.id,
        User.username,
        User.has_red_tag,
        func.count(Incident.id).label('incident_count')
    ).join(Incident, User.id == Incident.user_id).group_by(
        User.id
    ).order_by(func.count(Incident.id).desc()).limit(10).all()
    
    # Get incident status distribution
    status_stats = db.query(
        Incident.status,
        func.count(Incident.id).label('count')
    ).group_by(Incident.status).all()
    
    return {
        "severity_distribution": [
            {"severity": s[0], "count": s[1]} for s in severity_stats
        ],
        "daily_incidents": [
            {"date": str(d[0]), "count": d[1]} for d in daily_incidents
        ],
        "top_violators": [
            {
                "id": v[0],
                "username": v[1],
                "has_red_tag": v[2],
                "incident_count": v[3]
            } for v in top_violators
        ],
        "status_distribution": [
            {"status": s[0], "count": s[1]} for s in status_stats
        ]
    }
