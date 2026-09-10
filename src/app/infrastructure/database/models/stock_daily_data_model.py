from datetime import datetime, date
from sqlalchemy import DateTime, Float, String, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base
from app.infrastructure.database.types import Price

class StockDailyDataModel(Base):
    __tablename__ = "stock_daily_data"
    __table_args__ = (
      # A stock can appear once per (date, source) — e.g. the same symbol on the
      # same day from two different Chartink screeners is two rows, one per
      # screener label. Re-running the collector upserts the matching row.
      UniqueConstraint(
        "symbol", "trading_date", "source_type",
        name="uq_stock_daily_data_symbol_date_source",
      ),
    )

    id: Mapped[int] = mapped_column(
      primary_key=True,
      autoincrement=True,
    )
    symbol: Mapped[str] = mapped_column(
      String(32),
      index=True,
      nullable=False,
    )
    # Where this row came from: a Chartink screener key (see
    # `app/domain/entities/chartink_screeners.py`) or "excel_watchlist".
    source_type: Mapped[str] = mapped_column(
      String(64),
      index=True,
      nullable=False,
    )
    trading_date: Mapped[date] = mapped_column(
      Date,
      index=True,
      nullable=False,
    )
    open: Mapped[float | None] = mapped_column(
      Price,
      nullable=True,
    )
    high: Mapped[float | None] = mapped_column(
      Price,
      nullable=True,
    )
    low: Mapped[float | None] = mapped_column(
      Price,
      nullable=True,
    )
    close: Mapped[float | None] = mapped_column(
      Price,
      nullable=True,
    )
    # Day % change as reported by the source (Chartink screener). e.g. 7.0 = +7%.
    percent_change: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )

    volume: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    dividends: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    stock_splits: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      nullable=False,
    )
    # Get from NSE site API
    delivery_volume: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    delivery_percentage: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
