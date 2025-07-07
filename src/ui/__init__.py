# Standard library imports
import json
import logging
from typing import Any, Dict, List

# External library imports
import gradio as gr
import httpx

# Internal module imports
from src.settings import settings


# Configure module-level logging
logger = logging.getLogger(__name__)


def add_message(history: List[Dict[str, str]], message: str):
    """Add user message to chat history."""
    if message and message.strip():
        history.append({"role": "user", "content": message})
    return history, gr.Textbox(value=None)


async def bot(history: List[Dict[str, str]], clear_history: List[Dict[str, str]]):
    """Send message to FastAPI backend and get response."""
    if not history:
        return history, clear_history

    user_message = history[-1]["content"]

    try:
        request_data = {
            "message": user_message,
            "history": history[:-1],
            "clear_history": clear_history,
            "session_id": None,
            "user_id": None
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.fastapi.URL}/chat",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=120
            )

        if response.status_code == 200:
            result = response.json()
            assistant_msg = {"role": "assistant", "content": result["response"]}
            history.append(assistant_msg)
            clear_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in result["clear_history"]
            ]
            logger.info("Chatbot response received and history updated")
            return history, clear_history
        else:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            error_response = {"role": "assistant", "content": f"Произошла ошибка: {error_msg}"}
            history.append(error_response)
            return history, clear_history

    except Exception as e:
        error_message = (
            "Произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже или обратитесь в службу поддержки."
        )
        logger.exception(f"Error in bot function: {e}")
        error_response = {"role": "assistant", "content": error_message}
        history.append(error_response)
        return history, clear_history


async def handle_like_dislike(history: List[Dict[str, str]], x: gr.LikeData, feedback_storage: dict):
    """Handle like/dislike feedback by sending to FastAPI backend."""
    try:
        if len(history) <= x.index:
            logger.error(f"Invalid index {x.index} for history length {len(history)}")
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown(visible=False), feedback_storage

        q = history[x.index - 1]["content"] if x.index > 0 else ""
        a = history[x.index]["content"]

        if x.liked:
            feedback_data = {
                "score_name": "user-feedback",
                "question": q,
                "answer": a,
                "user_liked": True,
                "expected_output": None,
                "comment": None
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.fastapi.URL}/set_score",
                    json=feedback_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info("Positive feedback sent successfully")
                else:
                    logger.error(f"Failed to send feedback: {result.get('error')}")
            else:
                logger.error(f"API error sending feedback: {response.status_code}")
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown(visible=False), feedback_storage
        else:
            feedback_storage["question"] = q
            feedback_storage["answer"] = a
            feedback_storage["user_liked"] = False
            return (
                gr.Textbox(
                    placeholder="Как должен был ответить бот? (необязательно)",
                    visible=True,
                    value="",
                    label="Ваш предпочтительный ответ"
                ),
                gr.Button("Отправить отзыв", visible=True),
                gr.Markdown(visible=False),
                feedback_storage
            )

    except Exception as e:
        logger.exception(f"Error in like/dislike handler: {e}")
        return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown(visible=False), feedback_storage


async def submit_dislike_feedback(expected_output: str, feedback_storage: dict):
    """Submit dislike feedback with expected output."""
    try:
        if not feedback_storage:
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка: нет данных для отправки", visible=True), feedback_storage

        feedback_data = {
            "score_name": "user-feedback",
            "question": feedback_storage.get("question"),
            "answer": feedback_storage.get("answer"),
            "user_liked": False,
            "expected_output": expected_output.strip() if expected_output.strip() else None,
            "comment": None
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.fastapi.URL}/set_score",
                json=feedback_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info("Dislike feedback sent successfully")
                feedback_storage.clear()
                return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Спасибо за отзыв!", visible=True), feedback_storage
            else:
                logger.error(f"Failed to send feedback: {result.get('error')}")
                return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка при отправке", visible=True), feedback_storage
        else:
            logger.error(f"API error sending feedback: {response.status_code}")
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка при отправке", visible=True), feedback_storage

    except Exception as e:
        logger.exception(f"Error sending dislike feedback: {e}")
        return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка при отправке", visible=True), feedback_storage


with gr.Blocks(title="X5", fill_height=True) as ui_app:
    clear_history = gr.State([])
    feedback_storage = gr.State({})

    gr.Markdown(
        """
        # Чат поддержки X5
        Добро пожаловать в чат поддержки X5. Здесь вы можете задать любой вопрос, связанный с технической поддержкой, и получить ответ от бота. 
        Пожалуйста, используйте поле ввода ниже для отправки вашего вопроса.
        """
    )
    chatbot = gr.Chatbot(
        value=[],
        elem_id="chatbot",
        type="messages",
        autoscroll=True,
        show_copy_button=True,
        show_label=False,
    )

    chat_input = gr.Textbox(
        placeholder="Введите вопрос",
        interactive=True,
        show_label=False,
        submit_btn=True,
    )

    expected_output_input = gr.Textbox(
        placeholder="Как должен был ответить бот? (необязательно)",
        visible=False,
        label="Ваш предпочтительный ответ"
    )
    submit_feedback_btn = gr.Button("Отправить отзыв", visible=False)
    feedback_message = gr.Markdown(visible=False)

    clear = gr.ClearButton([chat_input, chatbot], value="Очистить")

    chat_msg = chat_input.submit(
        add_message, [chatbot, chat_input], [chatbot, chat_input], show_api=False
    )
    bot_msg = chat_msg.then(bot, [chatbot, clear_history], [chatbot, clear_history], api_name="bot_response")

    chatbot.like(
        handle_like_dislike,
        [chatbot, feedback_storage],
        [expected_output_input, submit_feedback_btn, feedback_message, feedback_storage],
        show_api=False
    )

    submit_feedback_btn.click(
        submit_dislike_feedback,
        [expected_output_input, feedback_storage],
        [expected_output_input, submit_feedback_btn, feedback_message, feedback_storage],
        show_api=False
    )


__all__ = ['ui_app']
