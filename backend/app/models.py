from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FeatureFlagType(str, Enum):
    """Supported feature flag value types.

    These values keep the schema explicit while allowing the application to
    validate incoming payloads consistently.
    """

    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"


class FeatureFlag(Base):
    """SQLAlchemy model for storing feature-flag metadata and runtime state.

    This model is intentionally designed for PostgreSQL-backed FastAPI
    applications and keeps the shape close to the Day 3 requirements:

    - `key`: unique logical identifier for the feature flag
    - `type`: the runtime data type expected for the flag value
    - `default_value`: the fallback value used when the flag is checked
    - `enabled`: whether the flag is currently active for the environment
    - `description`: optional business context for the feature flag
    - `owner_team`: responsible team for configuration and rollout
    - `environment_id`: environment scope for the feature flag
    """

    __tablename__ = "feature_flags"
    __table_args__ = (
        UniqueConstraint("key", "environment_id", name="uq_feature_flags_key_environment"),
    )

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    default_value = Column(JSON, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    rollout_percentage = Column(Integer, nullable=False, default=0)
    # List of user identifiers explicitly targeted to receive the flag
    target_users = Column(JSON, nullable=False, default=list)
    # List of group names explicitly targeted to receive the flag
    target_groups = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=True)
    owner_team = Column(String(100), nullable=False, index=True)
    environment_id = Column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"FeatureFlag(id={self.id!r}, key={self.key!r}, "
            f"type={self.type!r}, enabled={self.enabled!r})"
        )


class Environment(Base):
    """Persistent environment catalog used by the application and feature-flag overrides."""

    __tablename__ = "environments"
    __table_args__ = (UniqueConstraint("key", name="uq_environments_key"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"Environment(id={self.id!r}, key={self.key!r}, name={self.name!r})"


class FlagEnvironmentOverride(Base):
    """Environment-specific override values for a feature flag."""

    __tablename__ = "flag_environment_overrides"
    __table_args__ = (
        UniqueConstraint("flag_id", "environment_id", name="uq_flag_environment_override"),
    )

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(Integer, ForeignKey("feature_flags.id"), nullable=False, index=True)
    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    default_value = Column(JSON, nullable=False, default=False)
    rollout_percentage = Column(Integer, nullable=False, default=0)
    target_users = Column(JSON, nullable=False, default=list)
    target_groups = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"FlagEnvironmentOverride(flag_id={self.flag_id!r}, environment_id={self.environment_id!r}, "
            f"enabled={self.enabled!r})"
        )


class UserGroupMembership(Base):
    """Simple mapping table for user -> group membership used by the evaluation engine.

    Implemented minimally for Day 8 so the engine can resolve group membership
    without introducing a separate membership service.
    """

    __tablename__ = "user_group_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    group_name = Column(String(100), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"UserGroupMembership(user_id={self.user_id!r}, group_name={self.group_name!r})"
