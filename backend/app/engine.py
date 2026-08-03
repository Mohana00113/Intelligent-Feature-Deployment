from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import FeatureFlag

_ENVIRONMENT_MAP: dict[str, int] = {
    "development": 1,
    "staging": 2,
    "production": 3,
}


def _normalize_environment(environment: str | None) -> str:
    """Return a normalized environment name for lookup purposes."""

    if environment is None:
        return ""
    return environment.strip().lower()


def _resolve_environment_id(environment: str | None) -> int:
    """Map supported environment names to the legacy integer scope used by the model."""

    normalized = _normalize_environment(environment)
    environment_id = _ENVIRONMENT_MAP.get(normalized)
    if environment_id is None:
        raise ValueError(
            "Invalid environment. Supported values are: development, staging, production."
        )

    return environment_id


def evaluate_feature_flag(
    db: Session,
    key: str,
    environment: str | None,
    user_context: dict[str, Any] | None = None,
    include_reason: bool = False,
) -> dict[str, Any]:
    """Resolve a feature flag for the supplied environment.

    The evaluation flow first looks for an environment-scoped override. If none is
    present, it falls back to the baseline definition for the key. Empty or missing
    user context is ignored safely, which keeps the engine predictable for simple
    default-value checks.
    """

    _ = user_context or {}

    matching_flags = db.query(FeatureFlag).filter(FeatureFlag.key == key).all()
    if not matching_flags:
        raise KeyError(key)

    environment_id = _resolve_environment_id(environment)
    override_flag = next(
        (flag for flag in matching_flags if flag.environment_id == environment_id),
        None,
    )

    if override_flag is not None:
        resolved_flag = override_flag
    else:
        baseline_flag = next(
            (flag for flag in matching_flags if flag.environment_id == 1),
            None,
        )
        resolved_flag = baseline_flag or matching_flags[0]

    # Determine base resolution
    resolved = {
        "key": resolved_flag.key,
        "environment": _normalize_environment(environment),
        "enabled": bool(resolved_flag.enabled),
        "default_value": resolved_flag.default_value,
        "reason": None,
    }

    # If the feature is disabled globally for this record, note reason and set enabled False
    if not resolved_flag.enabled:
        resolved["reason"] = "feature_disabled"
        resolved["enabled"] = False
        if include_reason:
            return resolved
        return {
            "key": resolved["key"],
            "environment": resolved["environment"],
            "enabled": resolved["enabled"],
            "default_value": resolved["default_value"],
        }

    # User context may be empty
    ctx = user_context or {}

    # 1. User targeting (highest priority)
    try:
        target_users = resolved_flag.target_users or []
    except AttributeError:
        target_users = []

    user_id = ctx.get("user_id")
    if user_id is not None and user_id in target_users:
        resolved["enabled"] = True
        resolved["reason"] = "user_targeted"
        return resolved

    # TODO: group targeting and percentage rollout would go here (not implemented yet)

    # Fall back to enabled/default value
    resolved["reason"] = "default"
    if include_reason:
        return resolved

    # Backwards-compatible shape for callers that expect the original result
    return {
        "key": resolved["key"],
        "environment": resolved["environment"],
        "enabled": resolved["enabled"],
        "default_value": resolved["default_value"],
    }
