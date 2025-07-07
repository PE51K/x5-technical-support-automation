# Standard library imports
import logging

# Internal module imports
from ..workflow_events import DeduplicateEvent, RetrieveEvent


# Configure module-level logging
logger = logging.getLogger(__name__)


async def deduplicate_step(ev: RetrieveEvent) -> DeduplicateEvent:
    """Execute the deduplication step for the workflow.
    
    This step removes duplicate question-answer pairs based on answer content
    to ensure unique responses and avoid redundancy in the final result.
    
    Args:
        ev: RetrieveEvent containing retrieved question-answer pairs
        
    Returns:
        DeduplicateEvent containing deduplicated question-answer pairs
    """
    qa_pairs = ev.qa
    logger.info(f"Starting deduplication step with {len(qa_pairs)} QA pairs")
    
    unique_answers = set()
    deduplicated_qa_pairs = []
    
    for question, answer in qa_pairs:
        if answer in unique_answers:
            continue
        else:
            unique_answers.add(answer)
            deduplicated_qa_pairs.append((question, answer))
    
    duplicates_removed = len(qa_pairs) - len(deduplicated_qa_pairs)
    logger.info(f"Deduplication completed. Removed {duplicates_removed} duplicates, "
                f"keeping {len(deduplicated_qa_pairs)} unique QA pairs")
    
    return DeduplicateEvent(qa=deduplicated_qa_pairs)
