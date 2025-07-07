import logging
import uvicorn
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router as api_router
from ui import demo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="X5 Technical Support Automation",
    description="FastAPI backend with Gradio UI for X5 technical support automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api", tags=["api"])

# Mount Gradio app
app = gr.mount_gradio_app(app, demo, path="/")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "X5 Technical Support API is running"}

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {"status": "healthy", "message": "API endpoints are available"}

if __name__ == "__main__":
    logger.info("Starting X5 Technical Support Automation server...")
    uvicorn.run(app, host='0.0.0.0', port=8000)