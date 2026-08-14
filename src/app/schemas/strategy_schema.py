"""Pydantic request/response models for the strategies API."""

from pydantic import BaseModel


class StrategyRunRequest(BaseModel):
    """Request body for running one or more named strategies against all persisted stocks."""

    strategy_names: list[str]


class StrategyMatchRead(BaseModel):
    """Response shape for a single strategy evaluation result."""

    stock_symbol: str
    strategy_name: str
    matched: bool
    details: dict
