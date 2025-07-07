import gradio as gr
import httpx
import json
from typing import List, Dict, Any
import logging

from settings import settings

logger = logging.getLogger(__name__)


def add_message(history: List[Dict[str, str]], message: str):
    """Add user message to chat history."""
    if message is not None and message.strip() != "":
        history.append({"role": "user", "content": message})
    return history, gr.Textbox(value=None)

async def bot(history: List[Dict[str, str]], clear_history: List[Dict[str, str]]):
    """Send message to FastAPI backend and get response."""
    if not history:
        return history, clear_history
    
    user_message = history[-1]["content"]
    
    try:
        # Prepare request data
        request_data = {
            "message": user_message,
            "history": history[:-1],  # Exclude the current message
            "clear_history": clear_history,
            "session_id": None,  # You can add session management here
            "user_id": None
        }
        
        # Send request to FastAPI backend
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.fastapi.URL}/chat",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
        
        if response.status_code == 200:
            result = response.json()
            
            # Update history with assistant response
            assistant_msg = {"role": "assistant", "content": result["response"]}
            history.append(assistant_msg)
            
            # Update clear_history
            clear_history = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in result["clear_history"]
            ]
            
            print("\n--- History ---")
            for i, msg in enumerate(history):
                print(f"{i}: {msg['role']} - {msg['content']}")
            
            print("\n--- Clear History ---")
            for i, msg in enumerate(clear_history):
                print(f"{i}: {msg['role']} - {msg['content']}")
                
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

# Global storage for feedback data
feedback_storage = {}

async def print_like_dislike(history: List[Dict[str, str]], x: gr.LikeData):
    """Handle like/dislike feedback by sending to FastAPI backend."""
    try:
        if len(history) <= x.index:
            logger.error(f"Invalid index {x.index} for history length {len(history)}")
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown(visible=False)
        
        # Get question and answer from history
        q = history[x.index - 1]["content"] if x.index > 0 else ""
        a = history[x.index]["content"]
        
        # If user liked, send feedback immediately
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
                    logger.info(f"Positive feedback sent successfully")
                else:
                    logger.error(f"Failed to send feedback: {result.get('error')}")
            else:
                logger.error(f"API error sending feedback: {response.status_code}")
            
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown(visible=False)
        
        # If user disliked, store feedback data and show input for preferred answer
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
                gr.Markdown(visible=False)
            )
            
    except Exception as e:
        logger.exception(f"Error in like/dislike handler: {e}")
        return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown(visible=False)

async def submit_dislike_feedback(expected_output: str):
    """Submit dislike feedback with expected output."""
    try:
        if not feedback_storage:
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка: нет данных для отправки", visible=True)
        
        feedback_data = {
            "score_name": "user-feedback",
            "question": feedback_storage["question"],
            "answer": feedback_storage["answer"],
            "user_liked": False,
            "expected_output": expected_output if expected_output.strip() else None,
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
                logger.info(f"Dislike feedback sent successfully")
                feedback_storage.clear()
                return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Спасибо за отзыв!", visible=True)
            else:
                logger.error(f"Failed to send feedback: {result.get('error')}")
                return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка при отправке", visible=True)
        else:
            logger.error(f"API error sending feedback: {response.status_code}")
            return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка при отправке", visible=True)
            
    except Exception as e:
        logger.exception(f"Error sending dislike feedback: {e}")
        return gr.Textbox(visible=False), gr.Button(visible=False), gr.Markdown("Ошибка при отправке", visible=True)

# Create Gradio interface
with gr.Blocks(title="X5", fill_height=True) as ui_app:
    clear_history = gr.State([])

    title = gr.Markdown("# Чат поддержки X5")
    chatbot = gr.Chatbot(
        value=[
            {
                "role": "assistant",
                "content": 'Привет! Я бот поддержки X5. Можешь задать мне любой вопрос, например "Как выйти в отпуск?"',
            }
        ],
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

    # Components for dislike feedback (initially hidden)
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

    # Handle like/dislike with conditional UI for dislike
    chatbot.like(
        print_like_dislike,
        chatbot,
        [expected_output_input, submit_feedback_btn, feedback_message],
        show_api=False
    )
    
    # Handle dislike feedback submission
    submit_feedback_btn.click(
        submit_dislike_feedback,
        expected_output_input,
        [expected_output_input, submit_feedback_btn, feedback_message],
        show_api=False
    )

# Export the ui_app for mounting in FastAPI
__all__ = ['ui_app']