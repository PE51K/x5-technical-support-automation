# X5 Technical Support Automation - Refactored Architecture

This directory contains the refactored X5 Technical Support Automation system with a clean separation between FastAPI backend and Gradio frontend.

## 🏗️ Architecture Overview

```
src/
├── ai/                          # AI features and workflow logic
│   ├── __init__.py
│   ├── workflow.py              # Main AssistantFlow workflow
│   ├── workflow_with_tracing.py # Workflow with Langfuse tracing
│   ├── workflow_events.py       # Workflow event definitions
│   └── workflow_steps/          # Individual workflow steps
├── api/                         # FastAPI backend
│   ├── __init__.py
│   ├── chat.py                  # Chat and scoring endpoints
│   └── models.py                # Pydantic models
├── gradio/                      # Gradio UI
│   ├── __init__.py
│   └── ui.py                    # Gradio interface
├── settings.py                  # Configuration settings
├── app_with_gradio.py          # Main FastAPI app with mounted Gradio
└── Dockerfile                   # Updated Docker configuration
```

## 🚀 Running the Application

### Development
```bash
cd src
python app_with_gradio.py
```

### Docker
```bash
cd src
docker build -t x5-support .
docker run -p 8000:8000 x5-support
```

## 🔧 API Endpoints

- `GET /health` - Health check
- `GET /api/health` - API health check
- `POST /api/chat` - Process chat messages
- `POST /api/set_score` - Handle user feedback
- `/` - Gradio UI (mounted at root)

## 📝 Key Changes from Original

1. **Separation of Concerns**: AI logic, API, and UI are now in separate modules
2. **FastAPI Backend**: RESTful API endpoints for chat and feedback
3. **Gradio Frontend**: Clean UI that communicates with API via HTTP
4. **Better Structure**: Modular architecture for easier maintenance
5. **Docker Support**: Updated Dockerfile for the new structure

## 🔄 Request Flow

1. User input in Gradio UI
2. HTTP request to FastAPI `/api/chat` endpoint
3. API calls AI workflow (`run_workflow_with_tracing`)
4. Workflow processes query using existing logic
5. Response returned to API and then to UI
6. User feedback sent to `/api/set_score` endpoint

## 🧩 Original Logic Preserved

All original workflow logic from `ui.py` has been preserved:
- AI workflow steps remain unchanged
- Langfuse integration maintained
- Chat history management
- Like/dislike feedback system
- Error handling patterns

## 🔧 Configuration

The application uses the same `settings.py` file for configuration:
- Langfuse settings
- LLM settings
- Embeddings settings
- Qdrant settings

## 🐳 Docker Deployment

The updated Dockerfile:
- Exposes port 8000 (instead of 7860)
- Runs the FastAPI app with mounted Gradio
- Maintains the same build process with uv