import uvicorn
import gradio as gr

from api import api_app
from ui import ui_app
from settings import settings


if __name__ == "__main__":
    # Mount the Gradio app to the FastAPI app and run the server
    app = gr.mount_gradio_app(api_app, ui_app, path="/gradio")
    uvicorn.run(app, host='0.0.0.0', port=settings.fastapi.PORT)
