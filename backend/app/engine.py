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

    return {
        "key": resolved_flag.key,
        "environment": _normalize_environment(environment),
        "enabled": bool(resolved_flag.enabled),
        "default_value": resolved_flag.default_value,
    }
