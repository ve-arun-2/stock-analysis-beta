"""
Stocks endpoints.

Thin HTTP adapters: each handler resolves its dependencies via `Depends`
(see `app/api/deps.py`), delegates to a service, and maps the result to a
Pydantic schema. No business logic lives here.
"""
import logging
from fastapi import APIRouter, HTTPException

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
    """Collect stocks from the named source (see `infrastructure/sources/`) and persist them."""
    logger.info(f"=========: {request.source_name}" )
    if request.source_name is None:
        raise HTTPException(status_code=400, detail=f"Unknown source: {request.source_name}")

    stocks = await stock_service.collect_from_source(request.source_name)

    return stocks
