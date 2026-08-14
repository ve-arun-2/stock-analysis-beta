"""
EMA (Exponential Moving Average) strategy.

Flags stocks whose price is above their N-period EMA (N is typically 20, 50,
or 200 — see `EMAPeriod`). Phase 1 only wires up the shape; the actual price
history fetch and EMA calculation are added later.
"""

from enum import IntEnum

from app.domain.entities.stock import Stock, StrategyMatch


class EMAPeriod(IntEnum):
    """Supported EMA lookback periods."""

    SHORT = 20
    MEDIUM = 50
    LONG = 200


class EMAStrategy:
    """Matches stocks trading above their `period`-period EMA."""

    def __init__(self, period: EMAPeriod) -> None:
        self._period = period

    @property
    def name(self) -> str:
        return f"ema_{self._period.value}"

    async def evaluate(self, stocks: list[Stock]) -> list[StrategyMatch]:
        # Phase 2: fetch price history per stock, compute the EMA, and compare
        # against `stock.cmp`.
        raise NotImplementedError("EMA calculation will be implemented in a later phase.")
