"""
WebSocket endpoints for real-time chat
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, List
import json
import base64
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.message import Message
from app.models.incident import Incident, SeverityLevel
from app.models.friend_request import FriendRequest, FriendRequestStatus
from app.services.ai_detection import ai_detection_service
from app.services.evidence_logger import evidence_logger
from app.core.security import decode_access_token

router = APIRouter()

# Active connections: {user_id: WebSocket}
active_connections: Dict[int, WebSocket] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_user(self, message: dict, user_id: int):
        """Send message to a specific user if they're connected"""
        await self.send_personal_message(message, user_id)


manager = ConnectionManager()


async def get_user_from_token(token: str, db: Session) -> User:
    """Get user from WebSocket token"""
    try:
        payload = decode_access_token(token)
        if not payload:
            print("Invalid token payload")
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            print("No user_id in token")
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except Exception as e:
        print(f"Token validation error: {e}")
        return None


@router.websocket("/chat/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time chat"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        user = await get_user_from_token(token, db)
        
        if not user:
            print(f"WebSocket authentication failed for token: {token[:10]}...")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        await manager.connect(websocket, user.id)
        
        try:
            while True:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "message":
                    await handle_message(data, user, db)
                elif message_type == "typing":
                    await handle_typing(data, user)
                elif message_type == "read":
                    await handle_read(data, user, db)
        
        except WebSocketDisconnect:
            manager.disconnect(user.id)
        except Exception as e:
            print(f"WebSocket error for user {user.id}: {e}")
            manager.disconnect(user.id)
            
    finally:
        db.close()


async def handle_message(data: dict, sender: User, db: Session):
    """Handle incoming message"""
    receiver_id = data.get("receiver_id")
    content = data.get("content", "")
    message_type = data.get("message_type", "text")
    
    if not receiver_id or not content:
        return
    
    # Check friendship
    friendship = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == sender.id) & (FriendRequest.receiver_id == receiver_id)) |
        ((FriendRequest.sender_id == receiver_id) & (FriendRequest.receiver_id == sender.id)),
        FriendRequest.status == FriendRequestStatus.ACCEPTED
    ).first()
    
    if not friendship and receiver_id != sender.id:
        await manager.send_personal_message({
            "type": "error",
            "message": "Users must be friends to send messages"
        }, sender.id)
        return
    
    # AI Detection
    content_filtered = content
    is_flagged = False
    severity_score = None
    is_blocked = False
    detection_result = {}
    
    if message_type == "text":
        detection_result = await ai_detection_service.detect_text_abuse(
            content,
            sender.sensitivity_level.value
        )
        
        if detection_result["is_abusive"]:
            is_flagged = True
            severity_score = detection_result["severity"]
            content_filtered = detection_result["filtered_text"]
            
    elif message_type == "image":
        # Content is expected to be base64 encoded string
        try:
            # Remove header if present (e.g., "data:image/jpeg;base64,")
            if "," in content:
                header, encoded = content.split(",", 1)
            else:
                encoded = content
                
            image_data = base64.b64decode(encoded)
            detection_result = await ai_detection_service.detect_image_content(image_data)
            
            if not detection_result["is_safe"]:
                is_flagged = True
                severity_score = "high"  # Default for NSFW
                is_blocked = True  # Block unsafe images
                content_filtered = "[BLOCKED IMAGE]"
                detection_result["analysis"] = f"NSFW Content Detected: {', '.join(detection_result['categories'])}"
                detection_result["severity"] = "high"
        except Exception as e:
            print(f"Image decoding error: {e}")
            # Treat as text if decoding fails or just ignore
            pass

    if is_flagged:
        # Create incident
        incident = Incident(
            user_id=sender.id,
            severity=SeverityLevel(detection_result.get("severity", "medium")),
            detected_content=content[:500] if message_type == "text" else "[IMAGE]",
            ai_analysis=detection_result.get("analysis", "Flagged content"),
            detection_model="groq-llama" if message_type == "text" else "hf-nsfw",
            confidence_score=str(detection_result.get("confidence", 0.0))
        )
        db.add(incident)
        
        # Update warnings
        sender.warning_count += 1
        if sender.warning_count >= 3:
            sender.has_red_tag = True
        if sender.warning_count >= 5:
            sender.is_blocked = True
            is_blocked = True
        
        # Log evidence
        evidence_logger.log_incident(
            user_id=sender.id,
            message_id=None,
            severity=detection_result.get("severity", "medium"),
            detected_content=content if message_type == "text" else "[IMAGE]",
            ai_analysis=detection_result.get("analysis", "")
        )
        
        # Send warning to sender
        await manager.send_personal_message({
            "type": "warning",
            "message": f"Warning: Your message was flagged. Severity: {detection_result.get('severity', 'medium')}",
            "severity": detection_result.get("severity", "medium")
        }, sender.id)
    
    # Save message to database
    message = Message(
        sender_id=sender.id,
        receiver_id=receiver_id,
        content=content,
        content_filtered=content_filtered,
        message_type=message_type,
        is_flagged=is_flagged,
        severity_score=severity_score,
        is_blocked=is_blocked
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Send to receiver (only if not blocked)
    if not is_blocked:
        await manager.send_personal_message({
            "type": "message",
            "id": message.id,
            "sender_id": sender.id,
            "sender_username": sender.username,
            "content": content_filtered,
            "content_filtered": content_filtered,
            "content_original": content if not is_flagged else None,
            "message_type": message_type,
            "is_flagged": is_flagged,
            "severity_score": severity_score,
            "created_at": message.created_at.isoformat()
        }, receiver_id)
    
    # Send confirmation to sender
    await manager.send_personal_message({
        "type": "message_sent",
        "id": message.id,
        "receiver_id": receiver_id,
        "is_blocked": is_blocked,
        "created_at": message.created_at.isoformat()
    }, sender.id)


async def handle_typing(data: dict, user: User):
    """Handle typing indicator"""
    receiver_id = data.get("receiver_id")
    is_typing = data.get("is_typing", False)
    
    if receiver_id:
        await manager.send_personal_message({
            "type": "typing",
            "user_id": user.id,
            "username": user.username,
            "is_typing": is_typing
        }, receiver_id)


async def handle_read(data: dict, user: User, db: Session):
    """Handle read receipt"""
    message_id = data.get("message_id")
    
    if message_id:
        # Update message read status if needed
        await manager.send_personal_message({
            "type": "read",
            "message_id": message_id,
            "user_id": user.id
        }, user.id)

