"""Add persisted hourly evaluation metrics.

Revision ID: 20260826_add_evaluation_metrics
Revises: 20260826_add_audit_log
"""

from alembic import op
import sqlalchemy as sa

revision = "20260826_add_evaluation_metrics"
down_revision = "20260826_add_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "evaluation_metrics" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "evaluation_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flag_key", sa.String(length=100), nullable=False),
        sa.Column("hour", sa.DateTime(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("flag_key", "hour", name="uq_evaluation_metrics_flag_hour"),
    )
    op.create_index("ix_evaluation_metrics_flag_key", "evaluation_metrics", ["flag_key"])
    op.create_index("ix_evaluation_metrics_hour", "evaluation_metrics", ["hour"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_metrics_hour", table_name="evaluation_metrics")
    op.drop_index("ix_evaluation_metrics_flag_key", table_name="evaluation_metrics")
    op.drop_table("evaluation_metrics")