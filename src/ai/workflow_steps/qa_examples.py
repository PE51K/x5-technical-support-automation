# Standard library imports
import logging

# External library imports
from llama_index.core.workflow import Context, StopEvent

# Internal module imports
from ..workflow_events import HasQAExamplesEvent, SanityCheckEvent


# Configure module-level logging
logger = logging.getLogger(__name__)


async def is_there_qa_examples_step(
    ev: SanityCheckEvent, ctx: Context
) -> HasQAExamplesEvent | StopEvent:
    """Check if there are valid QA examples to proceed with response generation.
    
    This step evaluates whether the sanity check produced any valid question-answer
    pairs. If no examples are found, the workflow stops with an error message.
    If examples exist, the workflow continues to the response generation step.
    
    Args:
        ev: SanityCheckEvent containing validated QA pairs
        ctx: Context object for sharing data between workflow steps
        
    Returns:
        HasQAExamplesEvent if valid examples exist, StopEvent with error message otherwise
    """
    qa_pairs = ev.qa
    query_clean = await ctx.get("query_clean")
    
    logger.info(f"Checking QA examples availability. Found {len(qa_pairs)} pairs")
    
    if len(qa_pairs) == 0:
        error_message = (
            "К сожалению, у меня недостаточно информации, чтобы ответить на ваш запрос. "
            "Переключаю на оператора..."
        )
        
        logger.warning("No QA examples found - stopping workflow with error message")
        return StopEvent(result=(error_message, query_clean))
    else:
        logger.info(f"Found {len(qa_pairs)} valid QA examples - proceeding to response generation")
        return HasQAExamplesEvent(qa=qa_pairs)
