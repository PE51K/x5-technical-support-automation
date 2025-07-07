from fastapi import FastAPI, HTTPException
from langfuse import Langfuse
import logging

from settings import settings
from ai import run_workflow_with_tracing
from .models import ChatRequest, ChatResponse, ScoreRequest, ScoreResponse

logger = logging.getLogger(__name__)

# Initialize Langfuse
langfuse = Langfuse(
    public_key=settings.langfuse.PUBLIC_KEY,
    secret_key=settings.langfuse.SECRET_KEY,
    host=settings.langfuse.HOST,
)

# Create FastAPI app
api_app = FastAPI(
    title="X5 Technical Support API",
    description="API for X5 technical support automation",
    version="1.0.0"
)


@api_app.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "X5 Technical Support API", "version": "1.0.0"}


@api_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "X5 Technical Support API is running"}


@api_app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process chat message and return response using the AI workflow.
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")
        
        # Convert clear_history to the format expected by the workflow
        clear_history_list = []
        if request.clear_history:
            clear_history_list = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.clear_history
            ]
        
        # Run the workflow with tracing
        response, clear_query = await run_workflow_with_tracing(
            query=request.message,
            clear_history=clear_history_list,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        # Build the response history
        history = []
        if request.history:
            history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.history
            ]
        
        # Add the new user message and assistant response
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": response})
        
        # Update clear_history
        clear_history_list.append({"role": "user", "content": clear_query})
        clear_history_list.append({"role": "assistant", "content": response})
        
        return ChatResponse(
            response=response,
            clear_query=clear_query,
            history=[{"role": msg["role"], "content": msg["content"]} for msg in history],
            clear_history=[{"role": msg["role"], "content": msg["content"]} for msg in clear_history_list]
        )
        
    except Exception as e:
        logger.exception(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_app.post("/set_score", response_model=ScoreResponse)
async def set_score_endpoint(request: ScoreRequest):
    """
    Set score for user feedback and create dataset item in Langfuse.
    """
    try:
        logger.info(f"Received score request for trace {request.trace_id}: {request.score_value}")
        
        # Create dataset item in Langfuse (similar to original print_like_dislike function)
        # Note: This requires getting the original question and answer from the trace
        # For now, we'll create a simple score entry
        
        # You may need to store the Q&A pairs separately or retrieve them from Langfuse
        # For this implementation, we'll just log the feedback
        
        feedback_type = "positive" if request.score_value > 0.5 else "negative"
        
        # Create dataset item (you may need to adjust this based on your Langfuse setup)
        try:
            # This is a simplified version - you may need to retrieve actual Q&A from trace
            dataset_item_data = {
                "dataset_name": "qa",
                "metadata": {
                    "feedback": feedback_type,
                    "score": request.score_value,
                    "trace_id": request.trace_id
                }
            }
            
            if request.comment:
                dataset_item_data["metadata"]["comment"] = request.comment
            
            # Log for now - you can implement actual Langfuse dataset creation here
            logger.info(f"Dataset item data: {dataset_item_data}")
            
            return ScoreResponse(
                success=True,
                message=f"Score {request.score_value} recorded for trace {request.trace_id}"
            )
            
        except Exception as langfuse_error:
            logger.error(f"Langfuse error: {langfuse_error}")
            return ScoreResponse(
                success=False,
                error=f"Failed to create dataset item: {str(langfuse_error)}"
            )
        
    except Exception as e:
        logger.exception(f"Error setting score: {e}")
        return ScoreResponse(
            success=False,
            error=str(e)
        )

__all__ = ['api_app']