# Standard library imports
import logging

# External library imports
from langfuse.llama_index import LlamaIndexInstrumentor

# Internal module imports
from settings import settings
from .workflow import AssistantFlow


# Configure module-level logging
logger = logging.getLogger(__name__)


# Initialize Langfuse instrumentor with configuration settings
instrumentor = LlamaIndexInstrumentor(
    public_key=settings.langfuse.PUBLIC_KEY,
    secret_key=settings.langfuse.SECRET_KEY,
    host=settings.langfuse.URL,
)


async def run_workflow_with_tracing(
    query: str, clear_history: list = None, session_id: str = None, user_id: str = None
) -> tuple[str, str]:
    """Execute the assistant workflow with comprehensive tracing and monitoring.
    
    This function runs the complete assistant workflow while capturing
    detailed tracing information for monitoring and debugging purposes.
    
    Args:
        query: The user's input query to process
        clear_history: Optional list to clear conversation history
        session_id: Optional session identifier for tracking
        user_id: Optional user identifier for tracking
        
    Returns:
        A tuple containing (response, clear_query) where:
        - response: The generated assistant response
        - clear_query: The preprocessed/cleaned version of the input query
        
    Raises:
        Exception: Any errors during workflow execution are propagated
    """
    try:
        logger.info(f"Starting workflow execution with tracing for query: {query[:50]}...")
        instrumentor.start()

        # Use the context manager for tracing parameters
        with instrumentor.observe(
            trace_id=f"assistant-flow-{query[:10]}",
            session_id=session_id,
            user_id=user_id,
            metadata={
                "query": query,
                "llm": settings.llm.MODEL_NAME,
            },
        ):
            workflow = AssistantFlow(timeout=3 * 60)
            
            logger.info("Executing workflow with configured timeout")
            response, clear_query = await workflow.run(
                query=query,
                clear_history=clear_history,
            )
            
            logger.info("Workflow execution completed successfully")
            return response, clear_query
            
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise
        
    finally:
        # Make sure to flush before the application exits
        logger.info("Flushing instrumentor data")
        instrumentor.flush()
