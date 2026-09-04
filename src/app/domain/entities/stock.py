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
from enum import StrEnum


class StockSourceType(StrEnum):
    """Identifies which `StockSource` plugin produced a given stock."""

    EXCEL_WATCHLIST = "excel_watchlist"
    CHARTINK = "chartink"
    YAHOO_FINANCE = "yahoo_finance"
    NSE = "nse"


@dataclass
class Stock:
    """A single tradable instrument tracked by the platform (master/reference data),
    optionally carrying the point-in-time fields captured when a breakout alert
    fires (see `StockAlertRepository`)."""

    symbol: str
    company_name: str
    exchange: str = "NSE"
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    is_active: bool = True
    id: int | None = None  # None until persisted by a repository
    volume: int | None = None
    average_daily_10days_volume: int | None = None
    breakout_price: float | None = None
    breakout_volume_ratio: float | None = None


@dataclass
class StrategyMatch:
    """The outcome of evaluating one `Stock` against one `Strategy`."""

    stock: Stock
    strategy_name: str
    matched: bool
    details: dict = field(default_factory=dict)
