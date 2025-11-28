"""
Friend request schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FriendRequestCreate(BaseModel):
    receiver_id: int


class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FriendRequestUpdate(BaseModel):
    status: str  # accepted or rejected


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    has_red_tag: bool = False
    warning_count: int = 0
    is_blocked: bool = False
    
    class Config:
        from_attributes = True


class FriendRequestDetailResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    sender: UserResponse
    receiver: UserResponse

    class Config:
        from_attributes = True

