from datetime import datetime, date
from sqlalchemy import DateTime, Float, String, Date, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base

class StockTechnicalSnapshotModel(Base):
    __tablename__ = "stock_technical_snapshots"
    __table_args__ = (
        # One snapshot per stock per day; re-running the generator upserts it.
        UniqueConstraint(
            "symbol", "trading_date", name="uq_stock_technical_snapshots_symbol_date"
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
    trading_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )
    # -------------------------
    # Price
    # -------------------------
    close: Mapped[float | None] = mapped_column(Float)
    day_high: Mapped[float | None] = mapped_column(Float)
    day_low: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # 52 Week / All Time
    # -------------------------

    fifty_two_week_high: Mapped[float | None] = mapped_column(Float)
    fifty_two_week_low: Mapped[float | None] = mapped_column(Float)

    all_time_high: Mapped[float | None] = mapped_column(Float)
    all_time_low: Mapped[float | None] = mapped_column(Float)

    distance_from_52w_high_pct: Mapped[float | None] = mapped_column(Float)
    distance_from_52w_low_pct: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # SMA
    # -------------------------

    sma_20: Mapped[float | None] = mapped_column(Float)
    sma_50: Mapped[float | None] = mapped_column(Float)
    sma_100: Mapped[float | None] = mapped_column(Float)
    sma_200: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # EMA
    # -------------------------

    ema_9: Mapped[float | None] = mapped_column(Float)
    ema_20: Mapped[float | None] = mapped_column(Float)
    ema_50: Mapped[float | None] = mapped_column(Float)
    ema_100: Mapped[float | None] = mapped_column(Float)
    ema_200: Mapped[float | None] = mapped_column(Float)

    # Distance from EMA

    distance_from_ema_20_pct: Mapped[float | None] = mapped_column(Float)
    distance_from_ema_50_pct: Mapped[float | None] = mapped_column(Float)
    distance_from_ema_200_pct: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Price Returns
    # -------------------------

    change_1d_pct: Mapped[float | None] = mapped_column(Float)
    change_5d_pct: Mapped[float | None] = mapped_column(Float)
    change_10d_pct: Mapped[float | None] = mapped_column(Float)
    change_20d_pct: Mapped[float | None] = mapped_column(Float)
    change_50d_pct: Mapped[float | None] = mapped_column(Float)
    change_200d_pct: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Volume
    # -------------------------

    volume: Mapped[float | None] = mapped_column(Float)

    average_volume_5d: Mapped[float | None] = mapped_column(Float)
    average_volume_10d: Mapped[float | None] = mapped_column(Float)
    average_volume_20d: Mapped[float | None] = mapped_column(Float)
    average_volume_50d: Mapped[float | None] = mapped_column(Float)

    volume_ratio_5d: Mapped[float | None] = mapped_column(Float)
    volume_ratio_10d: Mapped[float | None] = mapped_column(Float)
    volume_ratio_20d: Mapped[float | None] = mapped_column(Float)
    volume_ratio_50d: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Momentum
    # -------------------------

    rsi_14: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # MACD
    # -------------------------

    macd: Mapped[float | None] = mapped_column(Float)
    macd_signal: Mapped[float | None] = mapped_column(Float)
    macd_histogram: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Volatility
    # -------------------------

    atr_14: Mapped[float | None] = mapped_column(Float)
    atr_14_pct: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Trend
    # -------------------------

    adx_14: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Bollinger Bands
    # -------------------------

    bollinger_upper: Mapped[float | None] = mapped_column(Float)
    bollinger_middle: Mapped[float | None] = mapped_column(Float)
    bollinger_lower: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Stochastic
    # -------------------------

    stochastic_k: Mapped[float | None] = mapped_column(Float)
    stochastic_d: Mapped[float | None] = mapped_column(Float)

    # -------------------------
    # Trend State
    # -------------------------

    price_above_ema_50: Mapped[bool | None] = mapped_column(Boolean)
    price_above_ema_200: Mapped[bool | None] = mapped_column(Boolean)

    golden_cross: Mapped[bool | None] = mapped_column(Boolean)
    death_cross: Mapped[bool | None] = mapped_column(Boolean)

    trend: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
