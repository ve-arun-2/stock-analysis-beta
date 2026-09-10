"""
Dependency-injection wiring.

This is the *only* file that should know how to construct concrete
repositories, sources, and services. Endpoints declare what they need via
`Depends(...)` from here; they never instantiate infrastructure classes
themselves. Swapping an implementation (e.g. a different repository backend)
means editing this file only.
"""

from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.stock_daily_data_repository import StockDailyDataRepository
from app.infrastructure.repositories.stock_repository import SqlAlchemyStockRepository
from app.infrastructure.strategies.registry import build_strategy_registry
from app.services.stock_service import StockService
from app.services.strategy_runner_service import StrategyRunnerService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return the shared `httpx.AsyncClient` created in the app lifespan (see `app/main.py`)."""
    return request.app.state.http_client


HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]


def get_stock_repository(session: DbSessionDep) -> SqlAlchemyStockRepository:
    """Provide the stock repository, backed by the SQLAlchemy adapter."""
    return SqlAlchemyStockRepository(session)


StockRepositoryDep = Annotated[SqlAlchemyStockRepository, Depends(get_stock_repository)]


def get_stock_daily_data_repository(session: DbSessionDep) -> StockDailyDataRepository:
    """Provide the daily-OHLCV repository, backed by the SQLAlchemy adapter."""
    return StockDailyDataRepository(session)


StockDailyDataRepositoryDep = Annotated[
    StockDailyDataRepository, Depends(get_stock_daily_data_repository)
]


def get_stock_service(
    repository: StockRepositoryDep,
    daily_data_repository: StockDailyDataRepositoryDep,
) -> StockService:
    """Provide the `StockService`, wired to the configured repositories."""
    return StockService(repository, daily_data_repository)


StockServiceDep = Annotated[StockService, Depends(get_stock_service)]


def get_strategy_runner_service() -> StrategyRunnerService:
    """Provide the `StrategyRunnerService` (currently stateless)."""
    return StrategyRunnerService()


StrategyRunnerServiceDep = Annotated[StrategyRunnerService, Depends(get_strategy_runner_service)]


def get_strategy_registry() -> dict:
    """Provide the name -> strategy factory registry (see `infrastructure/strategies/`)."""
    return build_strategy_registry()


StrategyRegistryDep = Annotated[dict, Depends(get_strategy_registry)]
