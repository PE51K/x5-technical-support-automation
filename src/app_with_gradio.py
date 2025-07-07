import logging
import uvicorn
import gradio as gr

from api import api_app
from ui import ui_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mount Gradio app on the API app
app = gr.mount_gradio_app(api_app, ui_app, path="/gradio")

if __name__ == "__main__":
    logger.info("Starting X5 Technical Support Automation server...")
    uvicorn.run(app, host='0.0.0.0', port=8000)