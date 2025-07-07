from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    clear_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    clear_query: str
    history: List[ChatMessage]
    clear_history: List[ChatMessage]


class ScoreRequest(BaseModel):
    trace_id: str
    score_name: str = "user-feedback"
    score_value: float  # 1.0 for like, 0.0 for dislike
    comment: Optional[str] = None


class ScoreResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None