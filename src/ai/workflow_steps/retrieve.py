from llama_index.core.workflow import Context
from ..workflow_events import PreprocessEvent, RetrieveEvent
from qdrant_client.http.models import ScoredPoint

from ai.retrieval import retrieval_manager


def process_points(points: list[ScoredPoint]) -> list[tuple[str, str]]:
    qa_tuples = [
        (point.payload["question_clear"], point.payload["content_clear"])
        for point in points
    ]
    return qa_tuples


def retriever(query_clean: str) -> list[tuple[str, str]]:
    points = retrieval_manager.retrieve(query_clean)
    search_result_clear = process_points(points)
    return search_result_clear


async def retrieve_step(ev: PreprocessEvent, ctx: Context) -> RetrieveEvent:
    query_clean = ev.query_clean
    await ctx.set("query_clean", query_clean)  # Saving clean query for use later
    
    # Get clear_history from context
    clear_history = await ctx.get("clear_history")
    
    # Get last 2 user messages from clear_history
    last_2_user_messages = [msg for msg in clear_history if msg["role"] == "user"][-2:]
    
    # Concatenate last 2 user messages with current query
    concatenated_query = "\n".join([msg["content"] for msg in last_2_user_messages] + [query_clean])
    print("Query to retrieve:", concatenated_query)
    
    qa = retriever(concatenated_query)
    return RetrieveEvent(qa=qa)
