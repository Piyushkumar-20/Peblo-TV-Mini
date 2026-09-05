"""enforce unique season per show"""

from alembic import op
import sqlalchemy as sa


revision = "85a5ddbf3f73"
down_revision = "0c4dceca5627"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_season_show_season_number",
        "seasons",
        ["show_id", "season_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_season_show_season_number",
        "seasons",
        type_="unique",
    )