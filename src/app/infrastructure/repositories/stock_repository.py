"""
SQLAlchemy-backed stock repository.

Translates between the domain `Stock` entity and the `StockModel` ORM row,
so no other layer needs to know that the storage is SQLAlchemy + PostgreSQL.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.stock import Stock, StockSourceType
from app.infrastructure.database.models.stock_model import StockModel


class SqlAlchemyStockRepository:
    """Persists and retrieves stocks using an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, stock: Stock) -> Stock:
        model = StockModel(
            symbol=stock.symbol,
            name=stock.name,
            exchange=stock.exchange,
            source=stock.source.value,
            cmp=stock.cmp,
            observed_at=stock.observed_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        result = await self._session.execute(select(StockModel).where(StockModel.symbol == symbol))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self) -> list[Stock]:
        result = await self._session.execute(select(StockModel))
        return [self._to_entity(model) for model in result.scalars().all()]

    @staticmethod
    def _to_entity(model: StockModel) -> Stock:
        """Map an ORM row to a framework-independent domain entity."""
        return Stock(
            id=model.id,
            symbol=model.symbol,
            name=model.name,
            exchange=model.exchange,
            source=StockSourceType(model.source),
            cmp=model.cmp,
            observed_at=model.observed_at,
        )
