"""Configuración centralizada de la aplicación con Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de configuración del sistema y servicios externos."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Entorno y servidor
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "1.0.0"
    PROJECT_NAME: str = "Enterprise AI Operations Assistant"

    # Almacenamiento local
    VECTOR_DB_PATH: str = "./data/vectorstore"
    SQLITE_DB_PATH: str = "./data/history.db"
    REQUESTS_DB_PATH: str = "./data/requests_db.json"

    # Proveedor LLM: "mock", "bedrock", "openai"
    LLM_PROVIDER: str = "mock"

    # AWS Bedrock
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: Optional[str] = "us-east-1"

    # OpenAI opcional
    OPENAI_API_KEY: Optional[str] = None

    # Parámetros de RAG
    SIMILARITY_THRESHOLD: float = 0.935  # Distancia máxima para considerar un fragmento relevante
    MAX_CONTEXT_CHUNKS: int = 4
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50


@lru_cache()
def get_settings() -> Settings:
    """Retorna una instancia singleton cacheada de la configuración."""
    return Settings()
