"""
Stock service.

Coordinates fetching stocks from a source plugin and persisting them via a
repository. Doesn't import any concrete source or repository class — it
just expects a `repository` with `add`/`get_by_symbol`/`list_all` and a
`source` with `name`/`fetch_stocks()`, matching the shapes in
`app/infrastructure/`. That keeps this file unchanged regardless of which
concrete source or database adapter is wired up (see `app/api/deps.py`).
"""
from fastapi import HTTPException, status
from app.core.logging import get_logger
from app.domain.entities.stock import Stock
from app.infrastructure.sources.excel_source import ExcelWatchlistSource

logger = get_logger(__name__)

class StockService:
    """Application service for collecting and persisting stocks."""

    def __init__(self, repository, alert_repository) -> None:
        self._repository = repository
        self._alert_repository = alert_repository

    async def init_source(self, source_name):
        """Build the source plugin matching `source_name`."""
        logger.info("collecting_stocks :", source=source_name)

        match source_name:
            case "excel_watchlist":
                return ExcelWatchlistSource(self._alert_repository)
            case _:
                raise ValueError(f"Unknown source: {source_name}")


    async def collect_from_source(self, source_name):
        try:
            fetchObj = await self.init_source(source_name)
            return await fetchObj.fetch_stocks()

        except Exception as err:
            logger.exception(f"Exception error in collect_from_source: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
            )

    async def list_stocks(self) -> list[Stock]:
        """Return every stock currently persisted."""
        return await self._repository.list_all()
