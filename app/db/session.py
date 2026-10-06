from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.db.base import Base

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initializes tables in database."""
    # Import all models to ensure they are registered with Base.metadata
    from app.models.lead import Tenant, Customer, Lead, ConversationMessage
    from app.models.analysis import LeadAnalysis
    from app.models.webhook import WebhookJob
    from app.models.follow_up import FollowUpLog

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
