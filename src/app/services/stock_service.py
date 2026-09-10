"""
Stock service.

Coordinates fetching stocks from a source plugin and persisting them via a
repository. The concrete repositories are constructed in `app/api/deps.py`
and injected here; this layer only calls the methods it needs
(`repository.list_all()`, etc.).
"""
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.domain.entities.stock import Stock
from app.infrastructure.repositories.stock_daily_data_repository import StockDailyDataRepository
from app.infrastructure.repositories.stock_repository import SqlAlchemyStockRepository
from app.infrastructure.sources.chartink_source import ChartinkSource
from app.infrastructure.sources.excel_source import ExcelWatchlistSource

logger = get_logger(__name__)

class StockService:
    """Application service for collecting and persisting stocks."""

    def __init__(
        self,
        repository: SqlAlchemyStockRepository,
        stock_daily_data_repo: StockDailyDataRepository,
    ) -> None:
        self._repository = repository
        self._stock_daily_data_repo = stock_daily_data_repo

    async def init_source(self, source_name: str):
        """Build the source plugin matching `source_name`."""
        logger.info("init_source", source=source_name)

        match source_name:
            case "excel_watchlist":
                return ExcelWatchlistSource(self._stock_daily_data_repo)
            case "chartink":
                # Runs every screener listed in CHARTINK_SCREENERS.
                return ChartinkSource(self._stock_daily_data_repo)
            case _:
                raise ValueError(f"Unknown source: {source_name}")

    async def collect_from_source(self, source_list: list[str]) -> list[Stock]:
        """Fetch stocks from each named source and return the combined list."""
        collected: list[Stock] = []
        for source_name in source_list:
            try:
                source = await self.init_source(source_name)
                stocks = await source.fetch_stocks()
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
                ) from err
            except Exception as err:
                logger.exception("collect_from_source_failed", source=source_name, error=str(err))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to collect from source: {source_name}",
                ) from err

            logger.info("collected_from_source", source=source_name, count=len(stocks))
            collected.extend(stocks)

        return collected

    async def list_stocks(self) -> list[Stock]:
        """Return every stock currently persisted."""
        return await self._repository.list_all()
