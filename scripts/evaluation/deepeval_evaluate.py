"""
Script for Evaluating LLM Traces with DeepEval and Logging Scores to Langfuse

This script fetches recent traces from Langfuse, processes each trace to extract
the cleaned query, answer, and context, evaluates the contextual relevancy of the
answer using DeepEval's ContextualRelevancyMetric, and writes the resulting score
back to Langfuse for each trace.

Environment variables required:
- LANGFUSE_PUBLIC_KEY
- LANGFUSE_SECRET_KEY
- LANGFUSE_HOST
- OPENAI_API_KEY

Usage:
    python deepeval_evaluate.py
"""

from dotenv import find_dotenv, load_dotenv
from datetime import datetime
from os import getenv
import os

from langfuse import Langfuse
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRelevancyMetric


# Load environment variables from .env file
load_dotenv(find_dotenv())

# Set OpenAI API key (should be set in your .env file)
os.environ['OPENAI_API_KEY'] = getenv("OPENAI_API_KEY", "")


def fetch_traces(langfuse, batch_size, from_timestamp):
    """
    Fetches a batch of traces from Langfuse starting from a given timestamp.
    """
    traces_batch = langfuse.fetch_traces(
        limit=batch_size,
        from_timestamp=from_timestamp,
    ).data
    return traces_batch


def process_context(qa_pairs):
    """
    Formats a list of question-answer pairs into a context string.
    """
    if not qa_pairs:
        return None
    context = []
    for pair in qa_pairs:
        context.append(f"Вопрос: {pair[0]}\nОтвет: {pair[1]}\n")
    return context


def process_trace(langfuse, trace):
    """
    Extracts relevant data (cleaned query, answer, context) from a trace.
    """
    trace_data = {'output': trace.output}
    for observation_id in trace.observations:
        if 'preprocess' in observation_id:
            observation = langfuse.fetch_observation(observation_id).data
            trace_data['query_clean'] = observation.output['query_clean']
        elif 'reply' in observation_id:
            observation = langfuse.fetch_observation(observation_id).data
            qa_pairs = observation.input.get('ev', {}).get('qa')
            context = process_context(qa_pairs)
            trace_data['context'] = context
    return trace_data


def evaluate_trace(langfuse, trace):
    """
    Evaluates a trace using DeepEval's ContextualRelevancyMetric.
    """
    trace_data = process_trace(langfuse, trace)
    query = trace_data.get('query_clean')
    answer = trace_data.get('output')
    context = trace_data.get('context')

    test_case = LLMTestCase(
        input=query,
        actual_output=answer,
        retrieval_context=context
    )
    contextual_relevancy_metric = ContextualRelevancyMetric(model="gpt-4o")

    # Evaluate the test case
    evaluate(
        test_cases=[test_case],
        metrics=[contextual_relevancy_metric]
    )
    score = contextual_relevancy_metric.score
    return score


def write_score(langfuse, trace_id, score):
    """
    Writes the evaluation score back to Langfuse for the given trace.
    """
    langfuse.score(
        trace_id=trace_id,
        name="contextual_relevancy",
        value=score
    )


if __name__ == "__main__":
    # Initialize Langfuse client
    langfuse = Langfuse(
        public_key=getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=getenv("LANGFUSE_SECRET_KEY"),
        host=getenv("LANGFUSE_HOST"),
    )

    # Set time window for fetching traces (from today 08:00)
    now = datetime.now()
    from_timestamp = datetime(now.year, now.month, now.day, 8, 0)
    batch_size = 10

    # Fetch traces and evaluate each one
    traces_batch = fetch_traces(langfuse, batch_size, from_timestamp)
    for trace in traces_batch:
        score = evaluate_trace(langfuse, trace)
        write_score(langfuse, trace_id=trace.id, score=score)
