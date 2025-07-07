from src.workflow_events import (
    SanityCheckEvent,
    HasQAExamplesEvent,
)

from llama_index.core.workflow import StopEvent
from llama_index.core.workflow import Context

async def is_there_qa_examples_step(
    ev: SanityCheckEvent,
    ctx: Context
) -> HasQAExamplesEvent | StopEvent:
    # Check if there are any QA examples
    qa = ev.qa
    query_clean = await ctx.get("query_clean")
    # If there are QA examples, continue
    if len(qa) == 0:
        return StopEvent(result=("К сожалению, у меня недостаточно информации, чтобы ответить на ваш запрос. Переключаю на оператора...", query_clean))
    # Else return GalaOtmena
    else:
        return HasQAExamplesEvent(qa=qa)
