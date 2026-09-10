"""
SQLAlchemy-backed repository for `stock_technical_snapshots`.

Writes one snapshot per (symbol, trading_date). Re-running the generator updates
the matching row rather than inserting a duplicate
(Postgres `INSERT ... ON CONFLICT DO UPDATE`).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.database.models.stock_technical_snapshot_model import (
    StockTechnicalSnapshotModel,
)

logger = get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")

_CONFLICT_TARGET = "uq_stock_technical_snapshots_symbol_date"
_KEY_COLUMNS = {"id", "symbol", "trading_date"}

# Everything except the identity/key columns is refreshed on conflict
# (including `calculated_at`).
_UPDATABLE_COLUMNS = tuple(
    column.name
    for column in StockTechnicalSnapshotModel.__table__.columns
    if column.name not in _KEY_COLUMNS
)


class StockTechnicalSnapshotRepository:
    """Persists technical snapshots using an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_snapshots(self, rows: list[dict]) -> int:
        """Insert or update the given snapshots. Each dict must carry `symbol`,
        `trading_date` and the indicator columns. Returns the number of rows sent."""
        if not rows:
            return 0

        calculated_at = datetime.now(IST)
        values = [{**row, "calculated_at": calculated_at} for row in rows]

        statement = pg_insert(StockTechnicalSnapshotModel).values(values)
        statement = statement.on_conflict_do_update(
            constraint=_CONFLICT_TARGET,
            set_={column: statement.excluded[column] for column in _UPDATABLE_COLUMNS},
        )

        await self._session.execute(statement)
        await self._session.commit()
        logger.info("stock_technical_snapshots_upserted", count=len(values))
        return len(values)
