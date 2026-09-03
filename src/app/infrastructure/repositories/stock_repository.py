"""
SQLAlchemy-backed stock repository.

Translates between the domain `Stock` entity and the `StockMasterModel` ORM
row, so no other layer needs to know that the storage is SQLAlchemy + PostgreSQL.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.stock import Stock
from app.infrastructure.database.models.stock_model import StockMasterModel


class SqlAlchemyStockRepository:
    """Persists and retrieves stocks using an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, stock: Stock) -> Stock:
        model = StockMasterModel(
            symbol=stock.symbol,
            company_name=stock.company_name,
            exchange=stock.exchange,
            sector=stock.sector,
            industry=stock.industry,
            market_cap=stock.market_cap,
            is_active=stock.is_active,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        result = await self._session.execute(
            select(StockMasterModel).where(StockMasterModel.symbol == symbol)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self) -> list[Stock]:
        result = await self._session.execute(select(StockMasterModel))
        return [self._to_entity(model) for model in result.scalars().all()]

    @staticmethod
    def _to_entity(model: StockMasterModel) -> Stock:
        """Map an ORM row to a framework-independent domain entity."""
        return Stock(
            id=model.id,
            symbol=model.symbol,
            company_name=model.company_name,
            exchange=model.exchange,
            sector=model.sector,
            industry=model.industry,
            market_cap=model.market_cap,
            is_active=model.is_active,
        )
