from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.stock_alert_trigger_model import StockAlertTriggerModel
from app.domain.entities.stock import Stock

IST = ZoneInfo("Asia/Kolkata")

class StockAlertRepository:

  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def add(self, stock: Stock):
    detected_at = datetime.now(IST)
    model = StockAlertTriggerModel(
      symbol=stock.symbol,
      company_name=stock.company_name,
      exchange=stock.exchange,
      detected_at=detected_at,
      breakout_date=detected_at.date(),
      breakout_price=stock.breakout_price,
      breakout_volume= stock.volume,
      average_daily_10days_volume= stock.average_daily_10days_volume
    )
    self._session.add(model)
    await self._session.commit()
    await self._session.refresh(model)