"""add_environment_support

Revision ID: 20260818_add_environment_support
Revises: 20260818_add_rollout_percentage
Create Date: 2026-08-18 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260818_add_environment_support"
down_revision = "20260818_add_rollout_percentage"
branch_labels = None
dependencies = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "environments" not in existing_tables:
        op.create_table(
            "environments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("key", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key", name="uq_environments_key"),
        )
        with op.batch_alter_table("environments") as batch_op:
            batch_op.create_index(batch_op.f("ix_environments_id"), ["id"], unique=False)
            batch_op.create_index(batch_op.f("ix_environments_name"), ["name"], unique=False)
            batch_op.create_index(batch_op.f("ix_environments_key"), ["key"], unique=True)

    if "flag_environment_overrides" not in existing_tables:
        op.create_table(
            "flag_environment_overrides",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("flag_id", sa.Integer(), nullable=False),
            sa.Column("environment_id", sa.Integer(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("default_value", sa.JSON(), nullable=False, server_default=sa.text("'false'")),
            sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("target_users", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("target_groups", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["flag_id"], ["feature_flags.id"]),
            sa.ForeignKeyConstraint(["environment_id"], ["environments.id"]),
            sa.UniqueConstraint("flag_id", "environment_id", name="uq_flag_environment_override"),
        )
        with op.batch_alter_table("flag_environment_overrides") as batch_op:
            batch_op.create_index(batch_op.f("ix_flag_environment_overrides_flag_id"), ["flag_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_flag_environment_overrides_environment_id"), ["environment_id"], unique=False)

    if "environments" in existing_tables:
        existing_env_keys = set(
            row[0]
            for row in bind.execute(sa.text("SELECT key FROM environments")).fetchall()
        )
        seed_values = [
            ("Development", "development", "Development environment"),
            ("Staging", "staging", "Staging environment"),
            ("Production", "production", "Production environment"),
        ]
        for name, key, description in seed_values:
            if key not in existing_env_keys:
                bind.execute(
                    sa.text(
                        "INSERT INTO environments (name, key, description, created_at, updated_at) VALUES (:name, :key, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    ),
                    {"name": name, "key": key, "description": description},
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "flag_environment_overrides" in existing_tables:
        op.drop_table("flag_environment_overrides")
    if "environments" in existing_tables:
        op.drop_table("environments")
