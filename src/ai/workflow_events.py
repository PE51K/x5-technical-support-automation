# Standard library imports
import logging

# External library imports
from llama_index.core.workflow import Event

# Internal module imports
# (none in this module)


# Configure module-level logging
logger = logging.getLogger(__name__)


class PreprocessEvent(Event):
    """Event containing preprocessed and cleaned query text."""
    
    query_clean: str


class RetrieveEvent(Event):
    """Event containing retrieved question-answer pairs from the database."""
    
    qa: list[tuple[str, str]]


class DeduplicateEvent(Event):
    """Event containing deduplicated question-answer pairs."""
    
    qa: list[tuple[str, str]]


class SanityCheckEvent(Event):
    """Event containing question-answer pairs that passed sanity checks."""
    
    qa: list[tuple[str, str]]


class HasQAExamplesEvent(Event):
    """Event containing validated question-answer pairs ready for response generation."""
    
    qa: list[tuple[str, str]]
