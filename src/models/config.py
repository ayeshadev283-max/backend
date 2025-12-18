"""Configuration models using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Cohere Configuration
    cohere_api_key: str = Field(..., env="COHERE_API_KEY")
    cohere_embedding_model: str = Field(
        default="embed-english-v3.0",
        env="COHERE_EMBEDDING_MODEL"
    )
    cohere_generation_model: str = Field(
        default="command-r",
        env="COHERE_GENERATION_MODEL"
    )
    cohere_max_tokens: int = Field(default=500, env="COHERE_MAX_TOKENS")
    cohere_temperature: float = Field(default=0.0, env="COHERE_TEMPERATURE")

    # Qdrant Configuration
    qdrant_url: str = Field(..., env="QDRANT_URL")
    qdrant_api_key: str = Field(default="", env="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(
        default="book_chunks_v1",
        env="QDRANT_COLLECTION_NAME"
    )

    # Postgres Configuration
    database_url: str = Field(..., env="DATABASE_URL")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Security Configuration
    api_key_enabled: bool = Field(default=False, env="API_KEY_ENABLED")
    api_key: str = Field(default="", env="API_KEY")

    # RAG Configuration
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=5, env="TOP_K_RETRIEVAL")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")

    # Rate Limiting
    rate_limit_per_hour: int = Field(default=60, env="RATE_LIMIT_PER_HOUR")

    # Development Mode (skip database connections)
    dev_mode: bool = Field(default=False, env="DEV_MODE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
