"""
Core domain entities for stocks and strategy evaluation.

These are plain Python `dataclasses` — intentionally independent of:
  - the SQLAlchemy row (`app/infrastructure/database/models/stock_model.py`)
  - the API request/response shape (`app/schemas/stock.py`)

Keeping these three representations separate means the database schema,
the public API contract, and the business rules can each change without
forcing changes in the other two.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class StockSourceType(StrEnum):
    """Identifies which `StockSource` plugin produced a given stock."""

    EXCEL_WATCHLIST = "excel_watchlist"
    CHARTINK = "chartink"
    YAHOO_FINANCE = "yahoo_finance"
    NSE = "nse"


@dataclass
class Stock:
    """A single tradable instrument tracked by the platform."""

    symbol: str
    name: str
    exchange: str = "NSE"
    source: StockSourceType = StockSourceType.EXCEL_WATCHLIST
    cmp: float | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None  # None until persisted by a repository


@dataclass
class StrategyMatch:
    """The outcome of evaluating one `Stock` against one `Strategy`."""

    stock: Stock
    strategy_name: str
    matched: bool
    details: dict = field(default_factory=dict)
