"""store show categories

Revision ID: 0c4dceca5627
Revises: 60842198e28f
Create Date: 2026-09-05 16:35:00.580993

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0c4dceca5627'
down_revision: Union[str, Sequence[str], None] = '60842198e28f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shows",
        sa.Column("categories", postgresql.JSONB(), nullable=True),
    )

    op.execute(
        """
        UPDATE shows
        SET categories = jsonb_build_array(category)
        """
    )

    op.alter_column(
        "shows",
        "categories",
        nullable=False,
    )

    op.drop_index("ix_shows_category", table_name="shows")
    op.drop_column("shows", "category")


def downgrade() -> None:
    op.add_column(
        "shows",
        sa.Column("category", sa.String(length=100), nullable=True),
    )

    op.execute(
        """
        UPDATE shows
        SET category = categories->>0
        """
    )

    op.alter_column(
        "shows",
        "category",
        nullable=False,
    )

    op.create_index(
        "ix_shows_category",
        "shows",
        ["category"],
    )

    op.drop_column("shows", "categories")
