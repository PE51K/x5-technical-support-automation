# Standard library imports
import logging

# External library imports
from fastapi import FastAPI, HTTPException
from langfuse import Langfuse

# Internal module imports
from ai import run_workflow_with_tracing
from settings import settings
from .models import ChatRequest, ChatResponse, ScoreRequest, ScoreResponse


# Configure module-level logging
logger = logging.getLogger(__name__)


# Initialize Langfuse for monitoring and feedback collection
langfuse_client = Langfuse(
    public_key=settings.langfuse.PUBLIC_KEY,
    secret_key=settings.langfuse.SECRET_KEY,
    host=settings.langfuse.URL,
)
langfuse_client.create_dataset("qa")

logger.info("Langfuse client initialized and dataset 'qa' created")


# Create FastAPI application instance
api_app = FastAPI(
    title="X5 Technical Support API",
    description="API for X5 technical support automation",
    version="1.0.0"
)

logger.info("FastAPI application initialized")


@api_app.get("/")
async def get_api_root():
    """API root endpoint providing basic service information.
    
    Returns:
        Basic service information including name and version
    """
    logger.info("API root endpoint accessed")
    return {
        "message": "X5 Technical Support API", 
        "version": "1.0.0"
    }


@api_app.get("/health")
async def perform_health_check():
    """Health check endpoint for service monitoring.
    
    Returns:
        Health status information for monitoring systems
    """
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy", 
        "message": "X5 Technical Support API is running"
    }


@api_app.post("/chat", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """Process chat message and return AI-generated response.
    
    This endpoint handles user chat messages, processes them through the AI workflow,
    and returns appropriate responses while maintaining conversation context.
    
    Args:
        request: ChatRequest containing user message and conversation context
        
    Returns:
        ChatResponse with AI-generated response and updated conversation history
        
    Raises:
        HTTPException: If processing fails due to internal errors
    """
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")
        
        # Convert conversation history to workflow format
        processed_clear_history = []
        if request.clear_history:
            processed_clear_history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.clear_history
            ]
        
        logger.info(f"Using {len(processed_clear_history)} messages from conversation history")
        
        # Execute AI workflow with tracing enabled
        ai_response, cleaned_query = await run_workflow_with_tracing(
            query=request.message,
            clear_history=processed_clear_history,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        logger.info("AI workflow completed successfully")
        
        # Build updated conversation history
        updated_history = []
        if request.history:
            updated_history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.history
            ]
        
        # Add current exchange to history
        updated_history.append({"role": "user", "content": request.message})
        updated_history.append({"role": "assistant", "content": ai_response})
        
        # Update processed conversation history
        processed_clear_history.append({"role": "user", "content": cleaned_query})
        processed_clear_history.append({"role": "assistant", "content": ai_response})
        
        logger.info("Conversation history updated successfully")
        
        return ChatResponse(
            response=ai_response,
            clear_query=cleaned_query,
            history=[
                {"role": msg["role"], "content": msg["content"]} 
                for msg in updated_history
            ],
            clear_history=[
                {"role": msg["role"], "content": msg["content"]} 
                for msg in processed_clear_history
            ]
        )
        
    except Exception as e:
        logger.exception(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_app.post("/set_score", response_model=ScoreResponse)
async def submit_user_feedback(request: ScoreRequest):
    """Submit user feedback and create dataset item for model improvement.
    
    This endpoint handles user feedback (likes/dislikes and suggestions) and
    creates appropriate dataset items in Langfuse for model training and evaluation.
    
    Args:
        request: ScoreRequest containing user feedback and context
        
    Returns:
        ScoreResponse indicating success or failure of the operation
    """
    try:
        logger.info(f"Processing user feedback: liked={request.user_liked}")
        
        # Prepare metadata for dataset item
        feedback_metadata = {
            "llm_model_name": settings.llm.MODEL_NAME,
            "user_liked": request.user_liked
        }
        
        if request.comment:
            feedback_metadata["comment"] = request.comment
            logger.info("User comment included in feedback")
        
        # Determine expected output based on user feedback
        expected_output = None
        if request.user_liked:
            # If user liked the response, use it as expected output
            expected_output = request.answer
            logger.info("Using assistant response as expected output (user liked)")
        elif request.expected_output and request.expected_output.strip():
            # If user disliked and provided suggestion, use their suggestion
            expected_output = request.expected_output
            logger.info("Using user suggestion as expected output (user disliked)")
        
        # Create dataset item in Langfuse
        langfuse_client.create_dataset_item(
            dataset_name="qa",
            input=request.question,
            expected_output=expected_output,
            metadata=feedback_metadata
        )
        
        logger.info("Dataset item created successfully in Langfuse")
        return ScoreResponse(
            success=True, 
            message="Dataset item created successfully"
        )
        
    except Exception as e:
        logger.exception(f"Error creating dataset item: {e}")
        return ScoreResponse(
            success=False, 
            error=str(e)
        )


__all__ = ['api_app']