# Standard library imports
import logging

# External library imports
import gradio as gr
import uvicorn

# Internal module imports
from api import api_app
from settings import settings
from ui import ui_app


# Configure module-level logging
logger = logging.getLogger(__name__)


def create_gradio_application():
    """Create and configure the Gradio application mounted on FastAPI.
    
    Returns:
        FastAPI application with Gradio UI mounted at /gradio path.
    """
    logger.info("Creating Gradio application mounted on FastAPI")
    gradio_app = gr.mount_gradio_app(api_app, ui_app, path="/gradio")
    return gradio_app


def start_application_server():
    """Start the application server with configured host and port.
    
    Uses settings from the FastAPI configuration to determine
    the host and port for the server.
    """
    application = create_gradio_application()
    
    logger.info(
        f"Starting application server on host=0.0.0.0, port={settings.fastapi.PORT}"
    )
    
    uvicorn.run(application, host='0.0.0.0', port=settings.fastapi.PORT)


if __name__ == "__main__":
    start_application_server()
