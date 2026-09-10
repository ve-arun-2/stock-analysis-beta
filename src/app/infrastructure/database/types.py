"""
Custom SQLAlchemy column types.
"""

from sqlalchemy import Float
from sqlalchemy.types import TypeDecorator


class Price(TypeDecorator):
    """A float column that rounds to 2 decimal places on write.

    Stored as `double precision`, exactly like `Float` — so switching a column
    between `Float` and `Price` needs no migration. The rounding happens for
    every write that goes through SQLAlchemy (ORM inserts, `insert().values()`,
    `ON CONFLICT DO UPDATE`).
    """

    impl = Float
    cache_ok = True

    def process_bind_param(self, value: object, dialect: object) -> float | None:
        if value is None:
            return None
        return round(float(value), 2)  # type: ignore[arg-type]
