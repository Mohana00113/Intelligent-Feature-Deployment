"""Add cleanup review markers and environment-scoped metrics.

Revision ID: 20260826_add_cleanup_tooling
Revises: 20260826_add_evaluation_metrics
"""

from alembic import op
import sqlalchemy as sa

revision = "20260826_add_cleanup_tooling"
down_revision = "20260826_add_evaluation_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "evaluation_metrics" in tables:
        columns = {column["name"] for column in inspector.get_columns("evaluation_metrics")}
        if "environment" not in columns:
            with op.batch_alter_table("evaluation_metrics") as batch_op:
                batch_op.add_column(sa.Column("environment", sa.String(length=100), nullable=False, server_default="development"))
                batch_op.drop_constraint("uq_evaluation_metrics_flag_hour", type_="unique")
                batch_op.create_unique_constraint("uq_evaluation_metrics_flag_environment_hour", ["flag_key", "environment", "hour"])
            op.create_index("ix_evaluation_metrics_environment", "evaluation_metrics", ["environment"])
    if "cleanup_reviews" not in tables:
        op.create_table(
            "cleanup_reviews",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("flag_key", sa.String(length=100), nullable=False),
            sa.Column("reviewed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("reviewed_by", sa.String(length=100), nullable=False, server_default="system"),
            sa.UniqueConstraint("flag_key"),
        )
        op.create_index("ix_cleanup_reviews_flag_key", "cleanup_reviews", ["flag_key"])


def downgrade() -> None:
    op.drop_index("ix_cleanup_reviews_flag_key", table_name="cleanup_reviews")
    op.drop_table("cleanup_reviews")
    bind = op.get_bind()
    if "evaluation_metrics" in set(sa.inspect(bind).get_table_names()):
        with op.batch_alter_table("evaluation_metrics") as batch_op:
            batch_op.drop_constraint("uq_evaluation_metrics_flag_environment_hour", type_="unique")
            batch_op.create_unique_constraint("uq_evaluation_metrics_flag_hour", ["flag_key", "hour"])
            batch_op.drop_column("environment")