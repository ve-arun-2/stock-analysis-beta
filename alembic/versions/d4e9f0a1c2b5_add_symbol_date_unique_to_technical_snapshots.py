"""add symbol+date unique constraint to stock_technical_snapshots

Revision ID: d4e9f0a1c2b5
Revises: b2f7c1a4d9e3
Create Date: 2026-09-10 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4e9f0a1c2b5'
down_revision: str | None = 'b2f7c1a4d9e3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_stock_technical_snapshots_symbol_date",
        "stock_technical_snapshots",
        ["symbol", "trading_date"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_stock_technical_snapshots_symbol_date",
        "stock_technical_snapshots",
        type_="unique",
    )
