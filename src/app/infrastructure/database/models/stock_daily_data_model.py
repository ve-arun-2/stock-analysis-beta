from datetime import datetime, date
from sqlalchemy import DateTime, Float, String, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base

class StockDailyDataModel(Base):
    __tablename__ = "stock_daily_data"

    id: Mapped[int] = mapped_column(
      primary_key=True,
      autoincrement=True,
    )
    symbol: Mapped[str] = mapped_column(
      String(32),
      index=True,
      nullable=False,
    )
    trading_date: Mapped[date] = mapped_column(
      Date,
      index=True,
      nullable=False,
    )
    open: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    high: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    low: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    close: Mapped[float | None] = mapped_column(
      Float,
      nullable=True,
    )
    adjusted_close: Mapped[float | None] = mapped_column(
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