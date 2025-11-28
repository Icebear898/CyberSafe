"""
Schemas for mental health support chatbot
"""
from typing import List, Literal, Optional
from pydantic import BaseModel


class SupportMessage(BaseModel):
    sender: Literal["user", "bot"]
    text: str


class MentalHealthRequest(BaseModel):
    message: str
    history: Optional[List[SupportMessage]] = []


class MentalHealthResponse(BaseModel):
    reply: str

