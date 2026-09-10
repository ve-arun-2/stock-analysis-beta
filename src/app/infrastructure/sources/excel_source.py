"""
Excel watchlist source.

Reads the symbol list from the watchlist workbook in S3, pulls each symbol's
latest daily bar from Yahoo Finance, and upserts it into `stock_daily_data`
with `source_type = "excel_watchlist"`. It does not write anything back to the
workbook and does not raise breakout alerts — that stays in `stock_monitor.py`.
"""

from app.core.logging import get_logger
from app.domain.entities.stock import Stock
from app.infrastructure.repositories.stock_daily_data_repository import (
    StockDailyDataRepository,
)
from app.infrastructure.sources.daily_data_ingest import IngestEntry, ingest_daily_bars
from app.infrastructure.sources.watchlist_client_common import read_watchlist_symbols

logger = get_logger(__name__)

SOURCE_TYPE = "excel_watchlist"


class ExcelWatchlistSource:
    """Collects the S3 watchlist symbols into `stock_daily_data`."""

    def __init__(self, stock_daily_data_repo: StockDailyDataRepository) -> None:
        self._stock_daily_data_repo = stock_daily_data_repo

    @property
    def name(self) -> str:
        return SOURCE_TYPE

    async def fetch_stocks(self) -> list[Stock]:
        symbols = read_watchlist_symbols()
        logger.info("excel_watchlist_symbols", count=len(symbols))

        entries = [IngestEntry(symbol=symbol, source_type=SOURCE_TYPE) for symbol in symbols]
        return await ingest_daily_bars(entries, self._stock_daily_data_repo)
