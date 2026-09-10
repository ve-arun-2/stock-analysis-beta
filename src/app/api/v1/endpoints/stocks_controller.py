"""
Stocks endpoints.

Thin HTTP adapters: each handler resolves its dependencies via `Depends`
(see `app/api/deps.py`), delegates to a service, and maps the result to a
Pydantic schema. No business logic lives here.
"""
import logging

from fastapi import APIRouter

from app.api.deps import StockServiceDep
from app.schemas.stock_schema import StockCollectRequest, StockRead

router = APIRouter()
logger = logging.getLogger(__name__)

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
    logger.info("collect_stocks requested: %s", request.source_list)
    return await stock_service.collect_from_source(request.source_list)

@router.get("/stocks/generate_technical_indicator", tags=["stocks"])
async def generate_technical_indicator(
    request: StockCollectRequest,
    stock_service: StockServiceDep,
):
    """Get stocks from table 'stock_daily_data' and generate indicator for those stocks."""
    
