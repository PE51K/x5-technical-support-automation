from langfuse.llama_index import LlamaIndexInstrumentor

from settings import settings
from .workflow import AssistantFlow


instrumentor = LlamaIndexInstrumentor(
    public_key=settings.langfuse.PUBLIC_KEY,
    secret_key=settings.langfuse.SECRET_KEY,
    host=settings.langfuse.URL,
)


async def run_workflow_with_tracing(
    query: str, clear_history: list = None, session_id: str = None, user_id: str = None
) -> tuple[str, str]:
    try:
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
            # result = await workflow.run(
            #     query=query,
            #     clear_history=clear_history,
            # )
            # print(result)
            # raise
            response, clear_query = await workflow.run(
                query=query,
                clear_history=clear_history,
            )
            return response, clear_query
    finally:
        # Make sure to flush before the application exits
        instrumentor.flush()
