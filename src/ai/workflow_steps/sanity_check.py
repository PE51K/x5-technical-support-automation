# Standard library imports
import asyncio
import json
import logging

# External library imports
import openai
from llama_index.core.workflow import Context

# Internal module imports
from src.settings import settings
from ..workflow_events import DeduplicateEvent, SanityCheckEvent


# Configure module-level logging
logger = logging.getLogger(__name__)


async def process_qa_batch(
    llm_client, query_clean: str, qa_batch: list[tuple[str, str]], 
    previous_user_messages: list[dict]
) -> list[tuple[str, str]]:
    """Process a single batch of QA pairs and return the relevant ones.
    
    Args:
        llm_client: OpenAI client for LLM API calls
        query_clean: Clean user query for relevance assessment
        qa_batch: Batch of question-answer pairs to evaluate
        previous_user_messages: Previous user messages for context
        
    Returns:
        List of relevant question-answer pairs
    """
    logger.info(f"Processing batch of {len(qa_batch)} QA pairs for relevance")
    
    # System prompt for grounded responses
    system_prompt = (
        "Твоя задача - определить, релевантны ли предоставленные документы запросу пользователя. "
        "Релевантым считай тот документ, в котором тема хотя бы смежно связана с запросом. "
        "Верни ровно один массив из строк '0' или '1', где '1' означает, что документ релевантен запросу, "
        "а '0' - что нерелевантен. Массив должен иметь ровно столько элементов, сколько документов в запросе."
    )

    # Extract message contents for context
    previous_messages_text = ", ".join([msg['content'] for msg in previous_user_messages])

    # Build messages based on model type
    if settings.llm.MODEL_NAME == "VikhrMODEL_NAMEs/Vikhr-Nemo-12B-Instruct-R-21-09-24":
        # Format QA pairs as documents for Vikhr model
        documents = []
        for idx, (question, answer) in enumerate(qa_batch):
            documents.append({"doc_id": idx, "title": question, "content": answer})

        user_content = (
            f"Прошлые сообщения пользователя: '{previous_messages_text}'. "
            f"Запрос пользователя: '{query_clean}'. "
            f"Оцени релевантность каждого документа к этому запросу с учетом контекста "
            f"и верни массив из {len(qa_batch)} элементов, где каждый элемент - '0' или '1'."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "documents", "content": json.dumps(documents, ensure_ascii=False)},
            {"role": "user", "content": user_content}
        ]
    
    elif settings.llm.MODEL_NAME == "google/gemma-2-9b-it":
        # Format for Google Gemma model
        documents_text = ""
        for idx, (question, answer) in enumerate(qa_batch):
            documents_text += f"Документ {idx}:\nВопрос: {question}\nОтвет: {answer}\n\n"

        user_content = (
            f"{system_prompt}\n\n"
            f"Документы:\n{documents_text}\n\n"
            f"Прошлые сообщения пользователя: '{previous_messages_text}'. "
            f"Запрос пользователя: '{query_clean}'. "
            f"Оцени релевантность каждого документа к этому запросу с учетом контекста "
            f"и верни массив из {len(qa_batch)} элементов, где каждый элемент - '0' или '1'."
        )

        messages = [
            {"role": "user", "content": user_content}
        ]

    else:
        # Default format for other models
        documents_text = ""
        for idx, (question, answer) in enumerate(qa_batch):
            documents_text += f"Документ {idx}:\nВопрос: {question}\nОтвет: {answer}\n\n"

        user_content = (
            f"Документы:\n{documents_text}\n\n"
            f"Прошлые сообщения пользователя: '{previous_messages_text}'. "
            f"Запрос пользователя: '{query_clean}'. "
            f"Оцени релевантность каждого документа к этому запросу с учетом контекста "
            f"и верни массив из {len(qa_batch)} элементов, где каждый элемент - '0' или '1'."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

    # Call the LLM API with guided JSON output
    response = await llm_client.chat.completions.create(
        model=settings.llm.MODEL_NAME,
        messages=messages,
        temperature=0.0,
        extra_body={
            "guided_json": {
                "type": "array",
                "items": {"type": "number", "enum": [0, 1]},
            }
        },
    )

    # Extract and parse response
    response_text = response.choices[0].message.content
    logger.info(f"Received LLM response: {response_text}")
    
    scores = list(map(int, json.loads(response_text)))
    logger.info(f"Parsed relevance scores: {scores}")

    # Ensure the length matches the batch size
    if len(scores) != len(qa_batch):
        if len(scores) < len(qa_batch):
            # If too short, extend with zeros
            scores.extend([0] * (len(qa_batch) - len(scores)))
        else:
            # If too long, truncate
            scores = scores[:len(qa_batch)]
        
        logger.warning(f"Adjusted scores length from {len(json.loads(response_text))} to {len(scores)}")

    # Filter QA pairs based on relevance scores
    filtered_qa_pairs = []
    for (question, answer), score in zip(qa_batch, scores):
        if score == 1:
            filtered_qa_pairs.append((question, answer))

    relevant_count = len(filtered_qa_pairs)
    logger.info(f"Found {relevant_count} relevant QA pairs out of {len(qa_batch)} in batch")
    
    return filtered_qa_pairs


async def perform_sanity_check(
    query_clean: str, qa_pairs: list[tuple[str, str]], previous_user_messages: list[dict]
) -> list[tuple[str, str]]:
    """Perform sanity check on question-answer pairs for relevance.
    
    Args:
        query_clean: Cleaned user query
        qa_pairs: List of question-answer pairs to check
        previous_user_messages: Previous user messages for context
        
    Returns:
        List of relevant question-answer pairs
    """
    logger.info(f"Starting sanity check for {len(qa_pairs)} QA pairs")
    
    # Initialize LLM client
    llm_client = openai.AsyncOpenAI(
        base_url=settings.llm.API_BASE_URL,
        api_key=settings.llm.API_KEY,
    )

    # Process QA pairs in batches for efficiency
    batch_size = 10
    batches = [
        qa_pairs[i:i + batch_size] for i in range(0, len(qa_pairs), batch_size)
    ]
    
    logger.info(f"Processing {len(batches)} batches of QA pairs")

    # Process all batches concurrently
    tasks = [
        process_qa_batch(llm_client, query_clean, batch, previous_user_messages) 
        for batch in batches
    ]
    batch_results = await asyncio.gather(*tasks)

    # Flatten results from all batches
    filtered_qa_pairs = [item for sublist in batch_results for item in sublist]
    
    logger.info(f"Sanity check completed. {len(filtered_qa_pairs)} relevant QA pairs "
                f"out of {len(qa_pairs)} total pairs")
    
    return filtered_qa_pairs


async def sanity_check_step(ev: DeduplicateEvent, ctx: Context) -> SanityCheckEvent:
    """Execute the sanity check step for the workflow.
    
    This step evaluates the relevance of deduplicated QA pairs against the user query
    using an LLM to filter out irrelevant content.
    
    Args:
        ev: DeduplicateEvent containing deduplicated QA pairs
        ctx: Context object for sharing data between workflow steps
        
    Returns:
        SanityCheckEvent containing relevance-filtered QA pairs
    """
    qa_pairs = ev.qa
    query_clean = await ctx.get("query_clean")
    
    logger.info("Starting sanity check step")
    
    # Get conversation history from context
    clear_history = await ctx.get("clear_history")
    
    # Extract last 2 user messages for context
    previous_user_messages = [
        msg for msg in clear_history if msg["role"] == "user"
    ][-2:] if clear_history else []
    
    # Perform relevance filtering
    relevant_qa_pairs = await perform_sanity_check(query_clean, qa_pairs, previous_user_messages)
    
    logger.info("Sanity check step completed successfully")
    return SanityCheckEvent(qa=relevant_qa_pairs)
