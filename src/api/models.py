# Standard library imports
import logging
from typing import Any, Dict, List, Optional

# External library imports
from pydantic import BaseModel


# Configure module-level logging
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Represents a single message in a chat conversation.
    
    Attributes:
        role: The role of the message sender (user, assistant, system)
        content: The actual message content
    """
    
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint containing user message and context.
    
    Attributes:
        message: The user's input message
        history: Optional conversation history for context
        clear_history: Optional processed/cleaned conversation history
        session_id: Optional session identifier for tracking
        user_id: Optional user identifier for tracking
    """
    
    message: str
    history: Optional[List[ChatMessage]] = None
    clear_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint containing assistant response and updated context.
    
    Attributes:
        response: The generated assistant response
        clear_query: The processed/cleaned version of the user's query
        history: Updated conversation history including the new exchange
        clear_history: Updated processed conversation history
    """
    
    response: str
    clear_query: str
    history: List[ChatMessage]
    clear_history: List[ChatMessage]


class ScoreRequest(BaseModel):
    """Request model for user feedback and scoring endpoint.
    
    Attributes:
        score_name: Name/type of the score being submitted
        question: The original user question being scored
        answer: The assistant's response being scored
        user_liked: Boolean indicating user satisfaction
        expected_output: Optional user suggestion for better response
        comment: Optional additional user feedback
    """
    
    score_name: str = "user-feedback"
    question: str
    answer: str
    user_liked: bool
    expected_output: Optional[str] = None
    comment: Optional[str] = None


class ScoreResponse(BaseModel):
    """Response model for scoring endpoint indicating operation success.
    
    Attributes:
        success: Boolean indicating if the operation succeeded
        message: Optional success message
        error: Optional error message if operation failed
    """
    
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    