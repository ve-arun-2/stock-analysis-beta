"""add source_type to stock_daily_data

Revision ID: b2f7c1a4d9e3
Revises: ac444a0f3818
Create Date: 2026-09-09 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f7c1a4d9e3'
down_revision: str | None = 'ac444a0f3818'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add nullable first, backfill any existing rows, then tighten to NOT NULL —
    # a straight NOT NULL add_column fails on a table that already has rows.
    op.add_column(
        "stock_daily_data",
        sa.Column("source_type", sa.String(length=64), nullable=True),
    )
    op.execute(
        "UPDATE stock_daily_data SET source_type = 'excel_watchlist' "
        "WHERE source_type IS NULL"
    )
    op.alter_column("stock_daily_data", "source_type", nullable=False)
    op.create_index(
        op.f("ix_stock_daily_data_source_type"),
        "stock_daily_data",
        ["source_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_stock_daily_data_symbol_date_source",
        "stock_daily_data",
        ["symbol", "trading_date", "source_type"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_stock_daily_data_symbol_date_source", "stock_daily_data", type_="unique"
    )
    op.drop_index(op.f("ix_stock_daily_data_source_type"), table_name="stock_daily_data")
    op.drop_column("stock_daily_data", "source_type")
