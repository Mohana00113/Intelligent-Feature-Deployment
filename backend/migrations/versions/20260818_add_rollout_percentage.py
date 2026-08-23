"""Add rollout percentage column to feature flags

Revision ID: 20260818_add_rollout_percentage
Revises:
Create Date: 2026-08-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260818_add_rollout_percentage"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("feature_flags")}
    if "rollout_percentage" not in existing_columns:
        with op.batch_alter_table("feature_flags") as batch_op:
            batch_op.add_column(sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("feature_flags")}
    if "rollout_percentage" in existing_columns:
        with op.batch_alter_table("feature_flags") as batch_op:
            batch_op.drop_column("rollout_percentage")
