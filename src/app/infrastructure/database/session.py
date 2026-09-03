"""
Async SQLAlchemy engine and session factory.

`get_session()` is an async generator meant to be wired up as a FastAPI
dependency (see `app/api/deps.py`) so each request gets its own session that
is closed automatically afterwards.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a request-scoped async database session."""
    async with AsyncSessionFactory() as session:
        yield session
