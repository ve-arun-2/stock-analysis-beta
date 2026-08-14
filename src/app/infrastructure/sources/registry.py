"""
Source registry.

A tiny factory that maps a source name to a constructed source instance.
Every source implements the same shape by convention (a `name` property and
an async `fetch_stocks()` method) rather than a formal interface. This is
the single place that needs a new line added when a new source plugin is
introduced — `app/api/deps.py` and the service layer never need to change.
"""

from collections.abc import Callable

import httpx

from app.core.config import Settings
from app.infrastructure.sources.chartink_source import ChartinkSource
from app.infrastructure.sources.excel_source import ExcelWatchlistSource
from app.infrastructure.sources.yahoo_finance_source import YahooFinanceSource

StockSourcePlugin = ExcelWatchlistSource | ChartinkSource | YahooFinanceSource


def build_source_registry(
    settings: Settings, http_client: httpx.AsyncClient
) -> dict[str, Callable[[], StockSourcePlugin]]:
    """Return a mapping of source name -> factory function for that source."""
    return {
        "excel_watchlist": lambda: ExcelWatchlistSource(settings.watchlist_excel_path),
        "chartink": lambda: ChartinkSource(
            base_url=settings.chartink_base_url,
            screener_clause="",  # Phase 2: populate from a request/config
            http_client=http_client,
        ),
        "yahoo_finance": lambda: YahooFinanceSource(
            base_url=settings.yahoo_finance_base_url,
            symbols=[],  # Phase 2: populate from a request/config
            http_client=http_client,
        ),
    }
