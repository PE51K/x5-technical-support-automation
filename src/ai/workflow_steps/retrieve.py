# Standard library imports
import logging

# External library imports
from llama_index.core.workflow import Context
from qdrant_client.http.models import ScoredPoint

# Internal module imports
from ai.retrieval import retrieval_manager
from ..workflow_events import PreprocessEvent, RetrieveEvent


# Configure module-level logging
logger = logging.getLogger(__name__)


def process_scored_points(points: list[ScoredPoint]) -> list[tuple[str, str]]:
    """Process Qdrant scored points into question-answer tuples.
    
    Args:
        points: List of scored points from Qdrant search
        
    Returns:
        List of tuples containing (question, answer) pairs
    """
    qa_tuples = [
        (point.payload["question_clear"], point.payload["content_clear"])
        for point in points
    ]
    
    logger.info(f"Processed {len(qa_tuples)} question-answer pairs from search results")
    return qa_tuples


def retrieve_similar_qa_pairs(query_clean: str) -> list[tuple[str, str]]:
    """Retrieve similar question-answer pairs from the knowledge base.
    
    Args:
        query_clean: Cleaned and preprocessed query text
        
    Returns:
        List of similar question-answer pairs
    """
    logger.info(f"Retrieving similar QA pairs for query: {query_clean[:50]}...")
    
    points = retrieval_manager.retrieve(query_clean)
    search_results = process_scored_points(points)
    
    logger.info(f"Retrieved {len(search_results)} similar QA pairs")
    return search_results


async def retrieve_step(ev: PreprocessEvent, ctx: Context) -> RetrieveEvent:
    """Execute the retrieval step for the workflow.
    
    This step retrieves relevant question-answer pairs from the knowledge base
    based on the preprocessed query. It also considers conversation history
    to provide better context for retrieval.
    
    Args:
        ev: PreprocessEvent containing the cleaned query
        ctx: Context object for sharing data between workflow steps
        
    Returns:
        RetrieveEvent containing retrieved question-answer pairs
    """
    query_clean = ev.query_clean
    await ctx.set("query_clean", query_clean)  # Save clean query for later use
    
    logger.info("Starting retrieval step")
    
    # Get conversation history from context
    clear_history = await ctx.get("clear_history")
    
    if clear_history:
        # Get last 2 user messages from conversation history
        last_user_messages = [
            msg for msg in clear_history if msg["role"] == "user"
        ][-2:]
        
        # Concatenate historical messages with current query for better context
        message_contents = [msg["content"] for msg in last_user_messages]
        concatenated_query = "\n".join(message_contents + [query_clean])
        
        logger.info(f"Using contextual query with {len(last_user_messages)} "
                   f"previous messages for retrieval")
    else:
        concatenated_query = query_clean
        logger.info("No conversation history available, using current query only")
    
    # Retrieve similar question-answer pairs
    qa_pairs = retrieve_similar_qa_pairs(concatenated_query)
    
    logger.info(f"Retrieval step completed with {len(qa_pairs)} results")
    return RetrieveEvent(qa=qa_pairs)
