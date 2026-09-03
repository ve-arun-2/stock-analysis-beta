from datetime import datetime, date
from sqlalchemy import DateTime, Float, String, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base

class StockFundamentalSnapshotModel(Base):
  __tablename__ = "stock_fundamental_snapshots"

  id: Mapped[int] = mapped_column(primary_key=True)

  symbol: Mapped[str] = mapped_column(
      String(32),
      index=True,
      nullable=False,
  )

  as_of_date: Mapped[date] = mapped_column(
    Date,
    index=True,
    nullable=False,
  )

  # Valuation
  market_cap: Mapped[float | None] = mapped_column(Float)
  pe_ratio: Mapped[float | None] = mapped_column(Float)
  forward_pe: Mapped[float | None] = mapped_column(Float)
  peg_ratio: Mapped[float | None] = mapped_column(Float)
  price_to_book: Mapped[float | None] = mapped_column(Float)

  # Profitability
  eps: Mapped[float | None] = mapped_column(Float)
  profit_margin: Mapped[float | None] = mapped_column(Float)
  operating_margin: Mapped[float | None] = mapped_column(Float)
  roe: Mapped[float | None] = mapped_column(Float)
  roa: Mapped[float | None] = mapped_column(Float)

  # Growth
  revenue_growth: Mapped[float | None] = mapped_column(Float)
  earnings_growth: Mapped[float | None] = mapped_column(Float)

  # Debt
  debt_to_equity: Mapped[float | None] = mapped_column(Float)

  # Dividend
  dividend_yield: Mapped[float | None] = mapped_column(Float)

  fetched_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
  )