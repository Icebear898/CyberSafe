"""
Message schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    receiver_id: int
    content: str
    message_type: str = "text"
    file_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    content_filtered: Optional[str]
    message_type: str
    file_url: Optional[str]
    is_flagged: bool
    severity_score: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

