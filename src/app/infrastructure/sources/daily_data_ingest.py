"""
Shared "symbols -> stock_daily_data" pipeline.

Both `ExcelWatchlistSource` and `ChartinkSource` end up with a list of
(symbol, source_type) pairs and need the same thing done with them: pull the
latest daily bar from Yahoo Finance and upsert it into `stock_daily_data`.
That logic lives here so it isn't duplicated in both sources.
"""

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

from app.core.logging import get_logger
from app.domain.entities.stock import Stock
from app.infrastructure.repositories.stock_daily_data_repository import (
    StockDailyDataRepository,
)
from app.infrastructure.sources.yfinance_client import fetch_daily_bar_yfinance

logger = get_logger(__name__)

_FETCH_CONCURRENCY = 8


@dataclass(frozen=True)
class IngestEntry:
    """One stock to collect, tagged with where it came from."""

    symbol: str
    source_type: str  # Chartink screener key, or "excel_watchlist"
    company_name: str | None = None
    percent_change: float | None = None  # day % change, if the source reports one


async def ingest_daily_bars(
    entries: Iterable[IngestEntry],
    repository: StockDailyDataRepository,
) -> list[Stock]:
    """Fetch a daily bar for every entry and upsert them all in one write.

    Fetches run concurrently (network bound); the DB write is a single
    statement. Entries whose bar can't be fetched are logged and skipped.
    """
    entry_list = list(entries)
    if not entry_list:
        return []

    semaphore = asyncio.Semaphore(_FETCH_CONCURRENCY)

    async def fetch(entry: IngestEntry) -> tuple[IngestEntry, dict | None]:
        async with semaphore:
            bar = await asyncio.to_thread(fetch_daily_bar_yfinance, entry.symbol)
        return entry, bar

    fetched = await asyncio.gather(*(fetch(entry) for entry in entry_list))

    rows: list[dict] = []
    stocks: list[Stock] = []
    for entry, bar in fetched:
        if bar is None:
            logger.warning(
                "daily_bar_unavailable", symbol=entry.symbol, source_type=entry.source_type
            )
            continue

        rows.append(
            {
                "symbol": entry.symbol,
                "source_type": entry.source_type,
                "trading_date": bar["trading_date"],
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
                "dividends": bar["dividends"],
                "stock_splits": bar["stock_splits"],
                "percent_change": entry.percent_change,
            }
        )
        stocks.append(
            Stock(
                symbol=entry.symbol,
                company_name=entry.company_name or entry.symbol,
                close=bar["close"],
                volume=bar["volume"],
                percent_change=entry.percent_change,
                source_type=entry.source_type,
            )
        )

    await repository.upsert_daily_bars(rows)
    logger.info("daily_bars_ingested", requested=len(entry_list), written=len(rows))
    return stocks
