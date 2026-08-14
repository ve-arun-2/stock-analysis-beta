"""
ORM model registry.

Import every model module here so `Base.metadata` (used by Alembic
autogeneration) knows about all of them.
"""

from app.infrastructure.database.models.stock_model import StockModel

__all__ = ["StockModel"]
