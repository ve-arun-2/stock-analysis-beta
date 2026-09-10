"""
SQLAlchemy-backed repository for `stock_daily_data`.

Writes one daily OHLCV bar per (symbol, trading_date, source_type). Re-running
the collector on the same day updates the matching row rather than inserting a
duplicate (Postgres `INSERT ... ON CONFLICT DO UPDATE`).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.database.models.stock_daily_data_model import StockDailyDataModel

logger = get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")

_CONFLICT_TARGET = "uq_stock_daily_data_symbol_date_source"

# Columns refreshed when a row for the same (symbol, trading_date, source_type)
# already exists. The key columns and `created_at` are left untouched.
_UPDATABLE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "dividends",
    "stock_splits",
    "percent_change",
)


class StockDailyDataRepository:
    """Persists daily OHLCV bars using an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_daily_bars(self, rows: list[dict]) -> int:
        """Insert or update the given bars. Each dict must carry `symbol`,
        `source_type`, `trading_date` and the OHLCV fields. Returns the number
        of rows sent."""
        if not rows:
            return 0

        created_at = datetime.now(IST)
        values = [{**row, "created_at": created_at} for row in rows]

        statement = pg_insert(StockDailyDataModel).values(values)
        statement = statement.on_conflict_do_update(
            constraint=_CONFLICT_TARGET,
            set_={column: statement.excluded[column] for column in _UPDATABLE_COLUMNS},
        )

        await self._session.execute(statement)
        await self._session.commit()
        logger.info("stock_daily_data_upserted", count=len(values))
        return len(values)
