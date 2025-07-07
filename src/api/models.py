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
    score_name: str = "user-feedback"
    question: str  # The user's original question (input)
    answer: str    # The assistant's response (output)
    user_liked: bool  # True for like, False for dislike
    expected_output: Optional[str] = None  # What the user thinks the response should be (optional)
    comment: Optional[str] = None


class ScoreResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None