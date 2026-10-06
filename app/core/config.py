import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Zizzet AI Lead Recovery Engine"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./zizzet_recovery.db"

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini", "ollama"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # LLM Retries & Backoff
    LLM_MAX_RETRIES: int = 3
    LLM_BACKOFF_FACTOR: float = 1.5

    # Active Prompt Version
    PROMPT_VERSION: str = "v1.0.0"

    # Queue Settings
    QUEUE_TYPE: str = "in_memory"  # "in_memory" or "redis"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Security & Multi-tenancy
    DEFAULT_TENANT_ID: Optional[str] = None
    REQUIRE_TENANT_HEADER: bool = False  # If true, X-Tenant-ID header is enforced

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
