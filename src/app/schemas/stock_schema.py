"""Pydantic request/response models for the stocks API."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

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
    """Request body for triggering a collection run from one or more sources."""

    source_list: list[StockSourceType] = Field(min_length=1)


class TechnicalIndicatorRequest(BaseModel):
    """Request body for generating technical snapshots from `stock_daily_data`.

    `trading_date` selects the day: every symbol that has a bar on that date is
    processed, using its history up to that date. Omit it to use today (IST).
    """

    trading_date: date | None = None
