"""
FastAPI application entrypoint.

Wires together settings, logging, middleware, and routers. Run locally with:
    uvicorn app.main:app --reload --app-dir src
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage resources that must live for the whole process (e.g. a shared HTTP client)."""
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("app_startup", app_name=settings.app_name, env=settings.app_env)
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        logger.info("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Long-term stock analysis platform: multi-source collection, "
    "pluggable strategies, and a future Agentic AI research layer. Not a trading bot.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
