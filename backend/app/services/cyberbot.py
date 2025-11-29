"""
CyberBOT Service - Automated warning system for policy violations
"""
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.message import Message


class CyberBOTService:
    """Service for sending automated warnings to users who violate policies"""
    
    CYBERBOT_USER_ID = 0  # System user ID for CyberBOT
    CYBERBOT_USERNAME = "CyberBOT"
    RED_TAG_THRESHOLD = 3  # Number of warnings before auto red-tag
    
    def __init__(self):
        self.warning_templates = {
            "cyberbullying": {
                "title": "⚠️ Cyberbullying Detected",
                "message": "We detected potentially harmful content in your recent message that may constitute cyberbullying. Please be respectful to others."
            },
            "hate_speech": {
                "title": "⚠️ Hate Speech Detected",
                "message": "Your message contained language that violates our hate speech policy. Please treat all users with respect."
            },
            "harassment": {
                "title": "⚠️ Harassment Detected",
                "message": "We detected harassing behavior in your recent message. Please maintain a positive environment."
            },
            "nsfw": {
                "title": "⚠️ Inappropriate Content Detected",
                "message": "Your message contained NSFW or inappropriate content. Please keep all content safe for work."
            },
            "profanity": {
                "title": "⚠️ Profanity Detected",
                "message": "Your message contained profanity or offensive language. Please communicate respectfully."
            },
            "default": {
                "title": "⚠️ Policy Violation Detected",
                "message": "We detected content that violates our community guidelines. Please review our policies."
            }
        }
    
    def generate_warning_message(
        self,
        violation_type: str,
        severity: str,
        warning_count: int,
        categories: list = None
    ) -> str:
        """Generate a contextual warning message"""
        
        # Get template
        template = self.warning_templates.get(
            violation_type.lower(),
            self.warning_templates["default"]
        )
        
        # Build warning message
        message_parts = [
            f"{template['title']}\n",
            f"{template['message']}\n",
            f"\n📊 Violation Details:",
            f"• Type: {violation_type.title()}",
            f"• Severity: {severity.upper()}",
        ]
        
        if categories:
            message_parts.append(f"• Categories: {', '.join(categories)}")
        
        message_parts.extend([
            f"\n⚠️ This is warning #{warning_count}.",
            ""
        ])
        
        # Add escalation warnings
        if warning_count >= self.RED_TAG_THRESHOLD:
            message_parts.extend([
                "🔴 Your account has been RED TAGGED due to repeated violations.",
                "Further violations may result in account suspension.",
            ])
        elif warning_count == self.RED_TAG_THRESHOLD - 1:
            message_parts.extend([
                f"⚠️ WARNING: One more violation will result in a RED TAG on your account.",
            ])
        else:
            message_parts.extend([
                f"Repeated violations may result in account restrictions.",
            ])
        
        message_parts.extend([
            "",
            "📖 Please review our Community Guidelines.",
            "💬 Need help? Talk to our AI Counselor in the Mental Health section.",
            "",
            "— CyberShield Safety Team"
        ])
        
        return "\n".join(message_parts)
    
    async def send_warning(
        self,
        db: Session,
        user_id: int,
        violation_type: str,
        severity: str,
        categories: list = None
    ) -> Dict:
        """Send warning message to user and update warning count"""
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Increment warning count
        if not hasattr(user, 'warning_count') or user.warning_count is None:
            user.warning_count = 0
        user.warning_count += 1
        
        # Auto red-tag if threshold reached
        if user.warning_count >= self.RED_TAG_THRESHOLD:
            user.has_red_tag = True
        
        # Generate warning message
        warning_text = self.generate_warning_message(
            violation_type,
            severity,
            user.warning_count,
            categories
        )
        
        # Create warning message in database
        warning_message = Message(
            sender_id=self.CYBERBOT_USER_ID,
            receiver_id=user_id,
            content=warning_text,
            content_filtered=warning_text,
            message_type="system_warning",
            is_flagged=False,
            severity_score="info",
            created_at=datetime.utcnow()
        )
        
        db.add(warning_message)
        db.commit()
        db.refresh(warning_message)
        db.refresh(user)
        
        return {
            "success": True,
            "warning_count": user.warning_count,
            "red_tagged": user.has_red_tag,
            "message_id": warning_message.id,
            "message": warning_text
        }


# Global instance
cyberbot_service = CyberBOTService()
