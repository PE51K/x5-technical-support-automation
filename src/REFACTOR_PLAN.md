# API Module Refactoring Plan

## Current Issue
The current architecture uses `APIRouter` in `src/api/chat.py`, but we need to remove the router and create a FastAPI app directly inside the API module.

## Required Changes

### 1. Update `src/api/chat.py`
- **Remove**: `from fastapi import APIRouter` 
- **Add**: `from fastapi import FastAPI`
- **Remove**: `router = APIRouter()`
- **Add**: `app = FastAPI()` 
- **Change**: All `@router.post(...)` decorators to `@app.post(...)`
- **Keep**: All existing endpoint logic unchanged

### 2. Update `src/api/__init__.py`
- **Remove**: `from .chat import router`
- **Add**: `from .chat import app`
- **Update**: `__all__ = ['app']` (instead of `['router']`)

### 3. Update `src/app_with_gradio.py`
- **Remove**: `from src.api import router as api_router`
- **Add**: `from src.api import app as api_app`
- **Remove**: `app.include_router(api_router, prefix="/api", tags=["api"])`
- **Add**: `app.mount("/api", api_app)`

### 4. Update import paths in `src/api/chat.py`
The current imports show:
```python
from settings import settings
from ai import run_workflow_with_tracing
```

These should be updated to:
```python
from src.settings import settings
from src.ai import run_workflow_with_tracing
```

## Benefits of This Change
1. **Simpler Architecture**: Direct FastAPI app instead of router
2. **Cleaner Mounting**: Mount the API app as a sub-application
3. **Better Separation**: API module is self-contained with its own FastAPI instance
4. **Easier Testing**: Can test the API module independently

## Implementation Steps
1. Modify `src/api/chat.py` to create FastAPI app instead of router
2. Update imports in `src/api/chat.py`
3. Update `src/api/__init__.py` exports
4. Update `src/app_with_gradio.py` to mount the API app
5. Test the endpoints at `/api/chat` and `/api/set_score`

## Expected Endpoint URLs
After refactoring:
- Main app: `http://localhost:8000`
- API health: `http://localhost:8000/api/` (if we add a root endpoint)
- Chat endpoint: `http://localhost:8000/api/chat`
- Score endpoint: `http://localhost:8000/api/set_score`
- Gradio UI: `http://localhost:8000` (mounted at root)