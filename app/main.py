import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, unhandled_exception_handler
from app.core.logging import correlation_id_ctx, logger, setup_logging
from app.db.session import init_db
from app.workers.lead_worker import process_webhook_lead_task
from app.workers.queue import job_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(debug=settings.DEBUG)
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")

    # Initialize Database tables
    await init_db()
    logger.info("Database schema initialized successfully.")

    # Register worker handler and start job queue
    job_queue.register_handler("process_webhook_lead", process_webhook_lead_task)
    await job_queue.start()

    yield

    # Shutdown
    logger.info("Shutting down background queues and resources...")
    await job_queue.stop()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Zizzet AI Lead Recovery Engine
    Identifies inactive or high-intent leads, analyzes conversation history with an LLM,
    and recommends the next best action plus personalized follow-ups.

    ### Core Capabilities:
    * **Structured AI Lead Scoring & Intent Classification** (`POST /api/v1/leads/analyze`)
    * **Tenant Isolation & Security** (Strict multi-tenant partitioning)
    * **Async Webhooks with Idempotency** (`POST /api/v1/webhooks/leads`)
    * **Lead Retrieval & Follow-up Generation** (`GET /api/v1/leads/{lead_id}/analysis`, `POST /api/v1/leads/{lead_id}/follow-up`)
    * **Opt-Out (DNC) Compliance** (Automatic suppression of follow-ups when lead opts out)
    * **Multi-Provider LLM Engine with Fallback & Exponential Retries** (Mock, OpenAI, Gemini, Ollama)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID Middleware for Request Tracing
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID") or f"corr_{uuid.uuid4().hex[:10]}"
    correlation_id_ctx.set(corr_id)

    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    return response


# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }
