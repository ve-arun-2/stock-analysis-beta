from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base

class StockAlertTriggerModel(Base):
    __tablename__ = "stock_alert_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    symbol: Mapped[str] = mapped_column(
        String(32),
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
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    # Calendar date (IST) `detected_at` falls on — lets multiple same-day
    # breakouts for a symbol be grouped/queried by day without re-deriving
    # it from `detected_at` (e.g. `where breakout_date = :today`). Not unique:
    # a symbol crossing 5 times in one day means 5 rows sharing this date.
    breakout_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    breakout_price: Mapped[float] = mapped_column(Float)

    # -------------------------
    # Volume at breakout
    # -------------------------

    breakout_volume: Mapped[float | None] = mapped_column(Float)

    breakout_volume_ratio: Mapped[float | None] = mapped_column(Float)

    average_daily_10days_volume: Mapped[int | None] = mapped_column(Integer)
    