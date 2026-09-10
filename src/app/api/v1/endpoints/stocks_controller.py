"""
Stocks endpoints.

Thin HTTP adapters: each handler resolves its dependencies via `Depends`
(see `app/api/deps.py`), delegates to a service, and maps the result to a
Pydantic schema. No business logic lives here.
"""

from fastapi import APIRouter

from app.api.deps import StockServiceDep, TechnicalIndicatorServiceDep
from app.core.logging import get_logger
from app.schemas.stock_schema import (
    StockCollectRequest,
    StockRead,
    TechnicalIndicatorRequest,
)

router = APIRouter()
logger = get_logger(__name__)

@router.get("/stocks", response_model=list[StockRead])
async def list_stocks(stock_service: StockServiceDep) -> list[StockRead]:
    """Return every stock currently persisted."""
    stocks = await stock_service.list_stocks()
    return [StockRead.model_validate(stock, from_attributes=True) for stock in stocks]


@router.post("/stocks/collect", tags=["stocks"])
async def collect_stocks(
    request: StockCollectRequest,
    stock_service: StockServiceDep,
):
    """Collect stocks from the named sources (see `infrastructure/sources/`)."""
    logger.info("collect_stocks_requested", sources=request.source_list)
    return await stock_service.collect_from_source(request.source_list)


@router.post("/stocks/generate_technical_indicator", tags=["stocks"])
async def generate_technical_indicator(
    request: TechnicalIndicatorRequest,
    service: TechnicalIndicatorServiceDep,
):
    """Compute technical snapshots for every stock in `stock_daily_data` on the
    given trading_date (default: today) and upsert them."""
    logger.info("generate_technical_indicator_requested", trading_date=request.trading_date)
    return await service.generate(request.trading_date)
