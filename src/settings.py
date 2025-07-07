# Standard library imports
import logging

# External library imports
from pydantic_settings import BaseSettings, SettingsConfigDict


# Configure module-level logging
logger = logging.getLogger(__name__)


class FastAPISettings(BaseSettings):
    """FastAPI server configuration settings."""
    
    HOST: str
    PORT: int

    model_config = SettingsConfigDict(
        env_prefix="FASTAPI_",
        env_file="../env/.env",
        extra='ignore'
    )

    @property
    def URL(self) -> str:
        """Generate the FastAPI server URL from host and port."""
        return f"http://{self.HOST}:{self.PORT}"


class LLMSettings(BaseSettings):
    """Large Language Model configuration settings."""
    
    API_BASE_URL: str
    MODEL_NAME: str
    API_KEY: str
    
    model_config = SettingsConfigDict(
        env_prefix="LLM_", 
        env_file="../env/.env",
        extra='ignore'
    )


class EmbedderSettings(BaseSettings):
    """Text embedding model configuration settings."""
    
    API_BASE_URL: str
    MODEL_NAME: str
    
    model_config = SettingsConfigDict(
        env_prefix="EMBEDDER_",
        env_file="../env/.env",
        extra='ignore'
    )


class LangfuseSettings(BaseSettings):
    """Langfuse tracing and monitoring configuration settings."""
    
    PUBLIC_KEY: str
    SECRET_KEY: str
    URL: str
    
    model_config = SettingsConfigDict(
        env_prefix="LANGFUSE_",
        env_file="../env/.env",
        extra='ignore'
    )


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration settings."""
    
    URL: str
    QA_COLLECTION_NAME: str
    TOP_N: int
    
    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        env_file="../env/.env",
        extra='ignore'
    )


class Settings(BaseSettings):
    """Main application settings container."""
    
    fastapi: FastAPISettings = FastAPISettings()
    llm: LLMSettings = LLMSettings()
    embedder: EmbedderSettings = EmbedderSettings()
    langfuse: LangfuseSettings = LangfuseSettings()
    qdrant: QdrantSettings = QdrantSettings()


# Singleton instance of Settings
settings = Settings()
