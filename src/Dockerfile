# Use a base Python image
FROM python:3.12-slim AS builder

# ENV vars
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the project configuration
COPY pyproject.toml .

# Install dependencies
RUN uv sync --only-group prod

# Copy the project
COPY . .

# Expose the port for FastAPI
EXPOSE 8000

# Run the FastAPI app with mounted Gradio
CMD ["python", "-m", "src.app_with_gradio"]
