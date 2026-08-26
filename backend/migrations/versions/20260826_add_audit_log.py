"""Add audit log table.

Revision ID: 20260826_add_audit_log
Revises: 20260818_add_environment_support
"""

from alembic import op
import sqlalchemy as sa

revision = "20260826_add_audit_log"
down_revision = "20260818_add_environment_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "audit_log" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("environment", sa.String(length=100), nullable=True),
        sa.Column("flag_key", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("previous_state", sa.JSON(), nullable=True),
        sa.Column("new_state", sa.JSON(), nullable=True),
        sa.Column("diff", sa.JSON(), nullable=False),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_log_actor", "audit_log", ["actor"])
    op.create_index("ix_audit_log_flag_key", "audit_log", ["flag_key"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_flag_key", table_name="audit_log")
    op.drop_index("ix_audit_log_actor", table_name="audit_log")
    op.drop_index("ix_audit_log_timestamp", table_name="audit_log")
    op.drop_table("audit_log")