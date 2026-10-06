from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health & Status"])


@router.get("/health", summary="Service Health Check")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER
    }


@router.get("/info", summary="Engine Architecture & Prompt Info")
async def info():
    return {
        "project": settings.PROJECT_NAME,
        "api_version": "v1",
        "prompt_version": settings.PROMPT_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "queue_type": settings.QUEUE_TYPE
    }
