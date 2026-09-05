"""add user password hash

Revision ID: add_user_password_hash
Revises: 85a5ddbf3f73
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa


revision = "add_user_password_hash"
down_revision = "85a5ddbf3f73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=500),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET password_hash =
            'pbkdf2_sha256$310000$bootstrap$bootstrap'
        WHERE password_hash IS NULL
        """
    )

    op.alter_column(
        "users",
        "password_hash",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("users", "password_hash")