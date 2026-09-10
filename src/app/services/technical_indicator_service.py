"""
Technical indicator service.

Reads the daily bars already stored in `stock_daily_data`, computes the
indicators defined by `StockTechnicalSnapshotModel` (via
`domain/entities/technical_indicators.py`), and upserts one snapshot per symbol
into `stock_technical_snapshots`.

It does not fetch any price history itself — indicators that need more history
than is stored come back as `None` and fill in as the collector accumulates rows.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.logging import get_logger
from app.domain.entities.technical_indicators import build_snapshot
from app.infrastructure.repositories.stock_daily_data_repository import StockDailyDataRepository
from app.infrastructure.repositories.stock_technical_snapshot_repository import (
    StockTechnicalSnapshotRepository,
)

logger = get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")


class TechnicalIndicatorService:
    """Generates technical snapshots from stored daily bars."""

    def __init__(
        self,
        daily_data_repo: StockDailyDataRepository,
        snapshot_repo: StockTechnicalSnapshotRepository,
    ) -> None:
        self._daily_data_repo = daily_data_repo
        self._snapshot_repo = snapshot_repo

    async def generate(self, trading_date: date | None = None) -> list[dict]:
        """Compute + upsert a snapshot for every symbol that has a bar on
        `trading_date` (default: today, IST). Each symbol's indicators use its
        history up to that date. Returns the upserted rows.
        """
        target = trading_date or datetime.now(IST).date()
        grouped = await self._daily_data_repo.list_bars_asof(target)

        rows: list[dict] = []
        for symbol, bars in grouped.items():
            if not bars:
                continue
            snapshot = build_snapshot(bars)
            snapshot["symbol"] = symbol
            rows.append(snapshot)

        await self._snapshot_repo.upsert_snapshots(rows)
        logger.info("technical_snapshots_generated", trading_date=str(target), symbols=len(rows))
        return rows
