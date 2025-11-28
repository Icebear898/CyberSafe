"""
AI Detection Service
Uses Groq for text analysis and HuggingFace for image/video detection
"""
import os
import base64
import json
import re
from typing import Dict, Optional, Tuple, List
from groq import Groq
from transformers import pipeline
from PIL import Image
import io
import numpy as np
from app.core.config import settings


class AIDetectionService:
    def __init__(self):
        self.groq_client = None
        self.image_classifier = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI services"""
        # Initialize Groq client
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"Warning: Could not initialize Groq client: {e}")
        
        # Initialize HuggingFace image classifier for NSFW detection
        # Using a model that detects inappropriate content
        try:
            if settings.HF_TOKEN:
                os.environ["HF_TOKEN"] = settings.HF_TOKEN
            # Using a lightweight model for NSFW detection
            # You can replace with more specific models like "Falconsai/nsfw_image_detection"
            self.image_classifier = pipeline(
                "image-classification",
                model="Falconsai/nsfw_image_detection",
                device=-1  # CPU, change to 0 for GPU
            )
        except Exception as e:
            print(f"Warning: Could not initialize image classifier: {e}")
            self.image_classifier = None
    
    async def detect_text_abuse(
        self, 
        text: str, 
        sensitivity_level: str = "medium"
    ) -> Dict:
        """
        Detect abusive content in text using Groq LLM
        Returns: {
            "is_abusive": bool,
            "severity": str,  # low, medium, high, critical
            "confidence": float,
            "categories": list,
            "filtered_text": str,
            "analysis": str
        }
        """
        if not self.groq_client:
            # Fallback to basic keyword detection
            return self._basic_text_detection(text, sensitivity_level)
        
        try:
            prompt = f"""Analyze the following message for cyberbullying, harassment, hate speech, sexual content, or inappropriate language.

Message: "{text}"

Provide a JSON response with:
1. is_abusive: boolean (true if abusive)
2. severity: string (one of: low, medium, high, critical)
3. confidence: float (0.0 to 1.0)
4. categories: array of strings (e.g., ["hate_speech", "harassment"])
5. filtered_text: string (replace offensive words with ***)
6. analysis: string (brief explanation)

Sensitivity level: {sensitivity_level}

Respond ONLY with valid JSON, no additional text."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an AI safety expert analyzing messages for harmful content. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            # Clean up content to ensure it's valid JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to find JSON object in the text
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("Could not parse JSON from response")
            
            return {
                "is_abusive": result.get("is_abusive", False),
                "severity": result.get("severity", "low"),
                "confidence": result.get("confidence", 0.0),
                "categories": result.get("categories", []),
                "filtered_text": result.get("filtered_text", text),
                "analysis": result.get("analysis", "")
            }
        except Exception as e:
            print(f"Error in Groq detection: {e}")
            return self._basic_text_detection(text, sensitivity_level)
    
    def _basic_text_detection(self, text: str, sensitivity_level: str) -> Dict:
        """Fallback basic keyword-based detection"""
        # Common offensive words (simplified list)
        offensive_keywords = [
            "hate", "kill", "die", "stupid", "idiot", "ugly", "fat", "loser"
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in offensive_keywords if kw in text_lower]
        
        is_abusive = len(found_keywords) > 0
        severity = "high" if len(found_keywords) > 2 else "medium" if found_keywords else "low"
        
        # Simple filtering
        filtered_text = text
        for kw in found_keywords:
            filtered_text = filtered_text.replace(kw, "***")
        
        return {
            "is_abusive": is_abusive,
            "severity": severity if is_abusive else "low",
            "confidence": 0.6 if is_abusive else 0.1,
            "categories": ["keyword_match"] if is_abusive else [],
            "filtered_text": filtered_text,
            "analysis": f"Detected {len(found_keywords)} potentially offensive keywords" if found_keywords else "No issues detected"
        }
    
    async def detect_image_content(
        self, 
        image_data: bytes
    ) -> Dict:
        """
        Detect inappropriate content in images
        Returns: {
            "is_safe": bool,
            "confidence": float,
            "categories": list,
            "nsfw_score": float
        }
        """
        if not self.image_classifier:
            # Fallback: basic check
            return {
                "is_safe": True,
                "confidence": 0.5,
                "categories": [],
                "nsfw_score": 0.0
            }
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Run classification
            results = self.image_classifier(image)
            
            # Parse results
            nsfw_score = 0.0
            categories = []
            
            for result in results:
                label = result.get("label", "").lower()
                score = result.get("score", 0.0)
                
                if "nsfw" in label or "porn" in label or "nude" in label or "sexy" in label:
                    nsfw_score = max(nsfw_score, score)
                    categories.append(label)
            
            is_safe = nsfw_score < 0.5  # Threshold for blocking
            
            return {
                "is_safe": is_safe,
                "confidence": nsfw_score if not is_safe else 1.0 - nsfw_score,
                "categories": categories,
                "nsfw_score": nsfw_score
            }
        except Exception as e:
            print(f"Error in image detection: {e}")
            return {
                "is_safe": True,  # Default to safe if error
                "confidence": 0.5,
                "categories": [],
                "nsfw_score": 0.0
            }
    
    def blur_offensive_words(self, text: str, offensive_words: list) -> str:
        """Blur offensive words in text"""
        filtered_text = text
        for word in offensive_words:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            filtered_text = pattern.sub("***", filtered_text)
        return filtered_text

    async def generate_support_response(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate an empathetic response for the mental health chatbot.
        History is a list of {"sender": "user"|"bot", "text": "..."} entries.
        """
        if not self.groq_client:
            return self._fallback_support_response(message)

        try:
            convo_history = history or []
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Aurora, a compassionate mental health support guide. "
                        "Respond with empathy, active listening, and practical coping tips. "
                        "Keep responses under 120 words, avoid giving medical advice, and "
                        "encourage seeking professional help when necessary."
                    ),
                }
            ]

            for entry in convo_history[-6:]:
                role = "assistant" if entry.get("sender") == "bot" else "user"
                messages.append({"role": role, "content": entry.get("text", "")})

            messages.append({"role": "user", "content": message})

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.4,
                max_tokens=300,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating support response: {e}")
            return self._fallback_support_response(message)

    def _fallback_support_response(self, message: str) -> str:
        """Simple deterministic fallback response"""
        return (
            "I hear you, and I'm here for you. It can help to take a deep breath and "
            "share as much or as little as you feel comfortable with. Would you like "
            "some grounding techniques or ways to reach out for support?"
        )


# Global instance
ai_detection_service = AIDetectionService()

