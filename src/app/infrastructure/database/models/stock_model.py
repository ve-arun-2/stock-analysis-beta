"""
SQLAlchemy ORM model for stocks.

This is the *database row shape*, distinct from the domain entity
(`app/domain/entities/stock.py`) and the API schema (`app/schemas/stock.py`).
The repository (`app/infrastructure/repositories/stock_repository.py`) is
responsible for converting between this model and the domain entity.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class StockModel(Base):
    """`stocks` table: one row per tracked instrument."""

    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(16), default="NSE")
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    cmp: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
