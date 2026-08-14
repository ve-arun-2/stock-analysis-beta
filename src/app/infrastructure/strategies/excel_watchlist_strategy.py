"""
Excel watchlist strategy.

Treats "present in the user's Excel watchlist" as a match. Distinct from
`ExcelWatchlistSource` (which reads the file): the source collects
candidates, this strategy decides whether each candidate qualifies. Phase 1
only wires up the shape.
"""

from app.domain.entities.stock import Stock, StrategyMatch


class ExcelWatchlistStrategy:
    """Matches stocks that appear in a named Excel watchlist."""

    def __init__(self, watchlist_name: str) -> None:
        self._watchlist_name = watchlist_name

    @property
    def name(self) -> str:
        return f"excel_watchlist_{self._watchlist_name}"

    async def evaluate(self, stocks: list[Stock]) -> list[StrategyMatch]:
        # Phase 2: cross-reference `stocks` against the parsed watchlist rows.
        raise NotImplementedError("Excel watchlist strategy will be implemented in a later phase.")
