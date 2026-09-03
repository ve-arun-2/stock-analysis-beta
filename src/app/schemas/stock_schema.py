"""Pydantic request/response models for the stocks API."""

from pydantic import BaseModel, ConfigDict

from app.domain.entities.stock import StockSourceType


class StockRead(BaseModel):
    """Response shape for a single stock (master/reference data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None
    symbol: str
    company_name: str
    exchange: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    is_active: bool


class StockCollectRequest(BaseModel):
    """Request body for triggering a collection run from a named source."""

    source_name: StockSourceType
