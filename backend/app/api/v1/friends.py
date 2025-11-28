"""
Friend request endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.friend_request import FriendRequest, FriendRequestStatus
from app.schemas.friend import (
    FriendRequestCreate,
    FriendRequestResponse,
    FriendRequestUpdate,
    UserResponse,
    FriendRequestDetailResponse,
)

router = APIRouter()


@router.post("/request", response_model=FriendRequestResponse)
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a friend request"""
    if request_data.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself"
        )
    
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == request_data.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if request already exists
    existing_request = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == request_data.receiver_id)) |
        ((FriendRequest.sender_id == request_data.receiver_id) & (FriendRequest.receiver_id == current_user.id))
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already exists"
        )
    
    # Create friend request
    friend_request = FriendRequest(
        sender_id=current_user.id,
        receiver_id=request_data.receiver_id,
        status=FriendRequestStatus.PENDING
    )
    
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    
    return friend_request


def _serialize_friend_request(request: FriendRequest) -> FriendRequestDetailResponse:
    return FriendRequestDetailResponse(
        id=request.id,
        status=request.status.value if isinstance(request.status, FriendRequestStatus) else request.status,
        created_at=request.created_at,
        sender=request.sender,
        receiver=request.receiver,
    )


@router.get("/requests", response_model=List[FriendRequestDetailResponse])
async def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all friend requests (sent and received)"""
    requests = db.query(FriendRequest).filter(
        (FriendRequest.sender_id == current_user.id) |
        (FriendRequest.receiver_id == current_user.id)
    ).all()
    
    return [_serialize_friend_request(req) for req in requests]


@router.get("/requests/received", response_model=List[FriendRequestDetailResponse])
async def get_received_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get received friend requests"""
    requests = db.query(FriendRequest).filter(
        FriendRequest.receiver_id == current_user.id,
        FriendRequest.status == FriendRequestStatus.PENDING
    ).all()
    
    return [_serialize_friend_request(req) for req in requests]


@router.put("/request/{request_id}", response_model=FriendRequestResponse)
async def respond_to_friend_request(
    request_id: int,
    update_data: FriendRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept or reject a friend request"""
    friend_request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.receiver_id == current_user.id
    ).first()
    
    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    if friend_request.status != FriendRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already processed"
        )
    
    if update_data.status == "accepted":
        friend_request.status = FriendRequestStatus.ACCEPTED
    elif update_data.status == "rejected":
        friend_request.status = FriendRequestStatus.REJECTED
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Use 'accepted' or 'rejected'"
        )
    
    db.commit()
    db.refresh(friend_request)
    
    return friend_request


@router.get("/list", response_model=List[UserResponse])
async def get_friends_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of friends (accepted friend requests)"""
    # Get all accepted friend requests where user is sender or receiver
    accepted_requests = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == current_user.id) |
         (FriendRequest.receiver_id == current_user.id)),
        FriendRequest.status == FriendRequestStatus.ACCEPTED
    ).all()
    
    # Extract friend IDs
    friend_ids = []
    for req in accepted_requests:
        if req.sender_id == current_user.id:
            friend_ids.append(req.receiver_id)
        else:
            friend_ids.append(req.sender_id)
    
    # Get friend users
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    
    return friends


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search users by username or email"""
    users = db.query(User).filter(
        (User.username.ilike(f"%{query}%")) |
        (User.email.ilike(f"%{query}%")),
        User.id != current_user.id
    ).limit(20).all()
    
    return users

