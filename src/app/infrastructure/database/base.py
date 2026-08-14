"""
SQLAlchemy declarative base.

Every ORM model (see `app/infrastructure/database/models/`) inherits from
`Base`. Alembic's `env.py` imports `Base.metadata` to autogenerate migrations,
so every new model module must be imported in
`app/infrastructure/database/models/__init__.py` to be picked up.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
