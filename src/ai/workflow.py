# Standard library imports
import logging

# External library imports
from llama_index.core.workflow import (
    Context,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

# Internal module imports
from .workflow_events import (
    DeduplicateEvent,
    HasQAExamplesEvent,
    PreprocessEvent,
    RetrieveEvent,
    SanityCheckEvent,
)
from .workflow_steps.deduplicate import deduplicate_step
from .workflow_steps.preprocess import preprocess_step
from .workflow_steps.qa_examples import is_there_qa_examples_step
from .workflow_steps.reply import reply_step
from .workflow_steps.retrieve import retrieve_step
from .workflow_steps.sanity_check import sanity_check_step


# Configure module-level logging
logger = logging.getLogger(__name__)


class AssistantFlow(Workflow):
    """Main workflow class that orchestrates the assistant's processing pipeline.
    
    This workflow handles the complete flow from query preprocessing through
    retrieval, deduplication, sanity checking, and response generation.
    """

    @step
    async def preprocess(self, ev: StartEvent, ctx: Context) -> PreprocessEvent:
        """Preprocess the incoming query and initialize workflow context.
        
        Args:
            ev: StartEvent containing the initial query and parameters
            ctx: Workflow context for sharing data between steps
            
        Returns:
            PreprocessEvent containing the cleaned query
        """
        # Get clear_history from StartEvent and save to Context
        clear_history = ev.clear_history
        await ctx.set("clear_history", clear_history)
        
        logger.info("Starting query preprocessing step")
        return await preprocess_step(ev)

    @step
    async def retrieve(self, ev: PreprocessEvent, ctx: Context) -> RetrieveEvent:
        """Retrieve relevant question-answer pairs from the database.
        
        Args:
            ev: PreprocessEvent containing the cleaned query
            ctx: Workflow context containing shared data
            
        Returns:
            RetrieveEvent containing retrieved QA pairs
        """
        logger.info("Starting question-answer retrieval step")
        return await retrieve_step(ev, ctx)

    @step
    async def deduplicate(self, ev: RetrieveEvent) -> DeduplicateEvent:
        """Remove duplicate question-answer pairs from retrieved results.
        
        Args:
            ev: RetrieveEvent containing retrieved QA pairs
            
        Returns:
            DeduplicateEvent containing deduplicated QA pairs
        """
        logger.info("Starting deduplication step")
        return await deduplicate_step(ev)

    @step
    async def sanity_check(self, ev: DeduplicateEvent, ctx: Context) -> SanityCheckEvent:
        """Perform sanity checks on the deduplicated question-answer pairs.
        
        Args:
            ev: DeduplicateEvent containing deduplicated QA pairs
            ctx: Workflow context containing shared data
            
        Returns:
            SanityCheckEvent containing validated QA pairs
        """
        logger.info("Starting sanity check step")
        return await sanity_check_step(ev, ctx)

    @step
    async def is_there_qa_examples(
        self, ev: SanityCheckEvent, ctx: Context
    ) -> HasQAExamplesEvent | StopEvent:
        """Check if there are valid QA examples to proceed with response generation.
        
        Args:
            ev: SanityCheckEvent containing validated QA pairs
            ctx: Workflow context containing shared data
            
        Returns:
            HasQAExamplesEvent if valid examples exist, StopEvent otherwise
        """
        logger.info("Checking for valid QA examples")
        return await is_there_qa_examples_step(ev, ctx)

    @step
    async def reply(self, ev: HasQAExamplesEvent, ctx: Context) -> StopEvent:
        """Generate the final response based on validated QA examples.
        
        Args:
            ev: HasQAExamplesEvent containing validated QA pairs
            ctx: Workflow context containing shared data
            
        Returns:
            StopEvent containing the final response
        """
        logger.info("Generating final response")
        return await reply_step(ev, ctx)
