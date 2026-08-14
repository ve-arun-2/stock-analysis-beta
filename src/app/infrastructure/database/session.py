"""
Async SQLAlchemy engine and session factory.

`get_session()` is an async generator meant to be wired up as a FastAPI
dependency (see `app/api/deps.py`) so each request gets its own session that
is closed automatically afterwards.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a request-scoped async database session."""
    async with AsyncSessionFactory() as session:
        yield session
