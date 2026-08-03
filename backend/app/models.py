from __future__ import annotations

from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Column, Integer, JSON, String, Text, UniqueConstraint
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
    description = Column(Text, nullable=True)
    owner_team = Column(String(100), nullable=False, index=True)
    environment_id = Column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"FeatureFlag(id={self.id!r}, key={self.key!r}, "
            f"type={self.type!r}, enabled={self.enabled!r})"
        )
