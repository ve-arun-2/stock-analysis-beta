"""
Chartink strategy.

Treats "was returned by a given Chartink screener" as a match. Distinct from
`ChartinkSource` (which fetches the stocks): the source collects candidates,
this strategy decides whether each candidate qualifies. Phase 1 only wires
up the shape.
"""

from app.domain.entities.stock import Stock, StrategyMatch


class ChartinkStrategy:
    """Matches stocks that satisfy a named Chartink screener clause."""

    def __init__(self, screener_name: str) -> None:
        self._screener_name = screener_name

    @property
    def name(self) -> str:
        return f"chartink_{self._screener_name}"

    async def evaluate(self, stocks: list[Stock]) -> list[StrategyMatch]:
        # Phase 2: cross-reference `stocks` against the latest Chartink
        # screener results for `self._screener_name`.
        raise NotImplementedError("Chartink strategy will be implemented in a later phase.")
