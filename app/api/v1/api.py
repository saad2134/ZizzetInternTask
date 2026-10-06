from fastapi import APIRouter
from app.api.v1.endpoints import health, leads, webhooks

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(leads.router)
api_router.include_router(webhooks.router)
