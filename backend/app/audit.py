from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, FeatureFlag, FlagEnvironmentOverride

_AUDITED_FIELDS = (
    "key",
    "type",
    "default_value",
    "enabled",
    "rollout_percentage",
    "target_users",
    "target_groups",
    "description",
    "owner_team",
    "environment_id",
)


def flag_state(flag: FeatureFlag) -> dict[str, Any]:
    """Return only non-sensitive feature flag configuration fields."""

    return {field: getattr(flag, field) for field in _AUDITED_FIELDS}


def override_state(override: FlagEnvironmentOverride) -> dict[str, Any]:
    """Return the effective configuration stored by an environment override."""

    return {
        "enabled": override.enabled,
        "default_value": override.default_value,
        "rollout_percentage": override.rollout_percentage,
        "target_users": override.target_users or [],
        "target_groups": override.target_groups or [],
        "description": override.description,
    }


def state_diff(previous: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    previous = previous or {}
    current = current or {}
    return {
        field: {"old": previous.get(field), "new": current.get(field)}
        for field in set(previous) | set(current)
        if previous.get(field) != current.get(field)
    }


def create_audit_log(
    db: Session,
    *,
    actor: str,
    environment: str | None,
    flag_key: str,
    action: str,
    previous_state: dict[str, Any] | None,
    new_state: dict[str, Any] | None,
) -> AuditLog:
    record = AuditLog(
        actor=actor or "system",
        environment=environment,
        flag_key=flag_key,
        action=action,
        previous_state=previous_state,
        new_state=new_state,
        diff=state_diff(previous_state, new_state),
    )
    db.add(record)
    return record