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

from app.infrastructure.database.session import Base


class StockMasterModel(Base):
    """`stocks master` table: one row has each NSE/BSE stock."""

    __tablename__ = "stocks_master"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    symbol: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    exchange: Mapped[str] = mapped_column(
        String(16),
        default="NSE",
        nullable=False,
    )
    sector: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    industry: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    market_cap: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
