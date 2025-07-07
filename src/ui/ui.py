import gradio as gr
import requests
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# FastAPI backend URL
API_BASE_URL = "http://localhost:8000/api"

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
        response = requests.post(
            f"{API_BASE_URL}/chat",
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

def print_like_dislike(history: List[Dict[str, str]], x: gr.LikeData):
    """Handle like/dislike feedback by sending to FastAPI backend."""
    try:
        if len(history) <= x.index:
            logger.error(f"Invalid index {x.index} for history length {len(history)}")
            return
        
        # Get question and answer from history
        q = history[x.index - 1]["content"] if x.index > 0 else ""
        a = history[x.index]["content"]
        
        # Determine score value
        score_value = 1.0 if x.liked else 0.0
        
        # Send feedback to API
        feedback_data = {
            "trace_id": f"gradio-feedback-{x.index}",  # You may want to use actual trace IDs
            "score_name": "user-feedback",
            "score_value": score_value,
            "comment": None
        }
        
        response = requests.post(
            f"{API_BASE_URL}/set_score",
            json=feedback_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info(f"Feedback sent successfully: {score_value}")
            else:
                logger.error(f"Failed to send feedback: {result.get('error')}")
        else:
            logger.error(f"API error sending feedback: {response.status_code}")
            
    except Exception as e:
        logger.exception(f"Error sending feedback: {e}")

# Create Gradio interface
with gr.Blocks(title="X5", fill_height=True) as demo:
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

    clear = gr.ClearButton([chat_input, chatbot], value="Очистить")

    chat_msg = chat_input.submit(
        add_message, [chatbot, chat_input], [chatbot, chat_input], show_api=False
    )
    bot_msg = chat_msg.then(bot, [chatbot, clear_history], [chatbot, clear_history], api_name="bot_response")

    chatbot.like(print_like_dislike, chatbot, None, show_api=False)

# Export the demo for mounting in FastAPI
__all__ = ['demo']