"""
ORM model registry.

Import every model module here so `Base.metadata` (used by Alembic
autogeneration) knows about all of them.
"""

from app.infrastructure.database.models.stock_alert_trigger_model import StockAlertTriggerModel
from app.infrastructure.database.models.stock_daily_data_model import StockDailyDataModel
from app.infrastructure.database.models.stock_model import StockMasterModel
from app.infrastructure.database.models.stock_technical_snapshot_model import StockTechnicalSnapshotModel

__all__ = [
    "StockAlertTriggerModel",
    "StockDailyDataModel",
    "StockMasterModel",
    "StockTechnicalSnapshotModel",
]
