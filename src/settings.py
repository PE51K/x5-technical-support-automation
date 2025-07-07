from pydantic_settings import BaseSettings, SettingsConfigDict


class FastAPISettings(BaseSettings):
    HOST: str
    PORT: int

    model_config = SettingsConfigDict(
        env_prefix="FASTAPI_",
        env_file="../env/.env",
        extra='ignore'
    )

    @property
    def URL(self) -> str:
        return f"http://{self.HOST}:{self.PORT}"


class LLMSettings(BaseSettings):
    API_BASE_URL: str
    MODEL_NAME: str
    API_KEY: str
    
    model_config = SettingsConfigDict(
        env_prefix="LLM_", 
        env_file="../env/.env",
        extra='ignore'
    )


class EmbedderSettings(BaseSettings):
    API_BASE_URL: str
    MODEL_NAME: str
    
    model_config = SettingsConfigDict(
        env_prefix="EMBEDDER_",
        env_file="../env/.env",
        extra='ignore'
    )


class LangfuseSettings(BaseSettings):
    PUBLIC_KEY: str
    SECRET_KEY: str
    URL: str
    
    model_config = SettingsConfigDict(
        env_prefix="LANGFUSE_",
        env_file="../env/.env",
        extra='ignore'
    )


class QdrantSettings(BaseSettings):
    URL: str
    QA_COLLECTION_NAME: str
    TOP_N: int
    
    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        env_file="../env/.env",
        extra='ignore'
    )


class Settings(BaseSettings):
    fastapi: FastAPISettings = FastAPISettings()
    llm: LLMSettings = LLMSettings()
    embedder: EmbedderSettings = EmbedderSettings()
    langfuse: LangfuseSettings = LangfuseSettings()
    qdrant: QdrantSettings = QdrantSettings()


# Singleton instance of Settings
settings = Settings()
