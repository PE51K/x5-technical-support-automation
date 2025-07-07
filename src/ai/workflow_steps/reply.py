# Standard library imports
import json
import logging

# External library imports
import openai
from llama_index.core.workflow import Context, StopEvent

# Internal module imports
from src.settings import settings
from ..workflow_events import HasQAExamplesEvent


# Configure module-level logging
logger = logging.getLogger(__name__)


async def generate_llm_response(
    query_clean: str, qa_examples: list[tuple[str, str]], conversation_history: list[dict] = None
) -> str:
    """Generate LLM response based on QA examples and conversation history.
    
    This function creates appropriate prompts based on the model type and generates
    a response using the provided question-answer examples as context.
    
    Args:
        query_clean: Cleaned user query
        qa_examples: List of relevant question-answer example pairs
        conversation_history: Previous conversation messages for context
        
    Returns:
        Generated response from the LLM
    """
    logger.info(f"Generating response for query: {query_clean[:50]}... "
                f"using {len(qa_examples)} QA examples")
    
    # Initialize LLM client
    llm_client = openai.AsyncOpenAI(
        base_url=settings.llm.API_BASE_URL,
        api_key=settings.llm.API_KEY,
    )

    # System prompt for response generation
    system_prompt = (
        "Ты помощник, который дает ответы на основе предоставленных примеров вопросов и ответов. "
        "Используй предоставленные вопросы и ответы как образец стиля и уровня детализации. "
        "Обращай внимание на прошлые сообщения для ответа на запрос пользователя. "
        "Не задавай уточняющих вопросов. "
        "Если примеры вопросов и ответов не содержат релевантной для запроса информации, "
        "не придумывай ответ, а дай знать пользователю."
    )

    # Ensure conversation history exists
    if conversation_history is None:
        conversation_history = []

    # Build messages based on model type
    if settings.llm.MODEL_NAME == "Vikhrmodels/Vikhr-Nemo-12B-Instruct-R-21-09-24":
        # Format QA pairs as documents for Vikhr model
        documents = []
        for idx, (question, answer) in enumerate(qa_examples):
            documents.append({
                "doc_id": idx, 
                "question": question, 
                "answer": answer
            })

        # Build message sequence
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.extend([
            {"role": "documents", "content": json.dumps(documents, ensure_ascii=False)},
            {"role": "user", "content": query_clean}
        ])

    elif settings.llm.MODEL_NAME == "google/gemma-2-9b-it":
        # Format for Google Gemma model
        examples_text = ""
        for idx, (question, answer) in enumerate(qa_examples):
            examples_text += f"Пример {idx+1}:\nВопрос: {question}\nОтвет: {answer}\n\n"

        # Combine conversation history with current query
        messages = conversation_history + [{"role": "user", "content": query_clean}]
        
        # Add examples to the last message
        messages[-1]["content"] = (
            f"Примеры вопросов и ответов:\n{examples_text}\n\n"
            f"Запрос пользователя: {messages[-1]['content']}"
        )
        
        # Add system prompt to the first message
        if messages:
            messages[0]["content"] = f"{system_prompt}\n\n{messages[0]['content']}"

    else:
        # Default format for other models
        examples_text = ""
        for idx, (question, answer) in enumerate(qa_examples):
            examples_text += f"Пример {idx+1}:\nВопрос: {question}\nОтвет: {answer}\n\n"
        
        # Build message sequence
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({
            "role": "user", 
            "content": (
                f"Примеры вопросов и ответов:\n{examples_text}\n\n"
                f"Запрос пользователя: {query_clean}"
            )
        })

    logger.info(f"Sending {len(messages)} messages to LLM for response generation")

    # Make API call to generate response
    response = await llm_client.chat.completions.create(
        model=settings.llm.MODEL_NAME,
        messages=messages,
        max_tokens=512,
        temperature=0.5,
    )

    generated_response = response.choices[0].message.content
    logger.info(f"Successfully generated response with {len(generated_response)} characters")
    
    return generated_response


async def reply_step(ev: HasQAExamplesEvent, ctx: Context) -> StopEvent:
    """Execute the reply generation step for the workflow.
    
    This final step generates the response using the validated QA examples
    and conversation history to provide a contextually appropriate answer.
    
    Args:
        ev: HasQAExamplesEvent containing validated QA examples
        ctx: Context object for sharing data between workflow steps
        
    Returns:
        StopEvent containing the generated response and clean query
    """
    qa_examples = ev.qa
    query_clean = await ctx.get("query_clean")
    conversation_history = await ctx.get("clear_history")
    
    logger.info("Starting reply generation step")
    
    # Generate the final response
    response = await generate_llm_response(query_clean, qa_examples, conversation_history)
    
    logger.info("Reply generation step completed successfully")
    return StopEvent(result=(response, query_clean))
