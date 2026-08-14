"""Pydantic request/response models for the stocks API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.entities.stock import StockSourceType


class StockRead(BaseModel):
    """Response shape for a single stock."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None
    symbol: str
    name: str
    exchange: str
    source: StockSourceType
    cmp: float | None
    observed_at: datetime


class StockCollectRequest(BaseModel):
    """Request body for triggering a collection run from a named source."""

    source_name: str
