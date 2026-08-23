from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy.orm import Session

from app.models import Environment, FeatureFlag, FlagEnvironmentOverride, UserGroupMembership

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


def evaluate_percentage_rollout(user_id: str, flag_key: str, rollout_percentage: int) -> bool:
    """Return whether a user should receive a percentage-based rollout for a flag."""

    if not isinstance(user_id, str) or not user_id:
        raise ValueError("user_id is required to evaluate percentage rollout.")
    if not isinstance(flag_key, str) or not flag_key:
        raise ValueError("flag_key is required to evaluate percentage rollout.")
    if not isinstance(rollout_percentage, int):
        rollout_percentage = int(rollout_percentage)
    if rollout_percentage < 0 or rollout_percentage > 100:
        raise ValueError("rollout_percentage must be between 0 and 100.")
    if rollout_percentage == 0:
        return False
    if rollout_percentage == 100:
        return True

    hash_input = f"{user_id}:{flag_key}".encode("utf-8")
    bucket = int(hashlib.sha256(hash_input).hexdigest(), 16) % 100
    return bucket < rollout_percentage


def _resolve_environment_config(db: Session, flag: FeatureFlag, environment: str | None) -> dict[str, Any]:
    """Return the effective config for a flag in the requested environment, preferring an override."""

    normalized_environment = _normalize_environment(environment)
    environment_name = normalized_environment or "development"
    env_record = db.query(Environment).filter(Environment.key == environment_name).first()
    if env_record is None:
        return {
            "enabled": bool(flag.enabled),
            "default_value": flag.default_value,
            "rollout_percentage": int(getattr(flag, "rollout_percentage", 0) or 0),
            "target_users": list(getattr(flag, "target_users", []) or []),
            "target_groups": list(getattr(flag, "target_groups", []) or []),
        }

    override = (
        db.query(FlagEnvironmentOverride)
        .filter(FlagEnvironmentOverride.flag_id == flag.id, FlagEnvironmentOverride.environment_id == env_record.id)
        .first()
    )

    if override is None:
        return {
            "enabled": bool(flag.enabled),
            "default_value": flag.default_value,
            "rollout_percentage": int(getattr(flag, "rollout_percentage", 0) or 0),
            "target_users": list(getattr(flag, "target_users", []) or []),
            "target_groups": list(getattr(flag, "target_groups", []) or []),
        }

    return {
        "enabled": bool(override.enabled),
        "default_value": override.default_value,
        "rollout_percentage": int(getattr(override, "rollout_percentage", 0) or 0),
        "target_users": list(getattr(override, "target_users", []) or []),
        "target_groups": list(getattr(override, "target_groups", []) or []),
    }


def evaluate_feature_flag_request(
    db: Session,
    flag_key: str,
    environment: str,
    user_id: str,
    group: str | None = None,
) -> dict[str, Any]:
    """Evaluate a runtime request using the Day 11 rule priority."""

    normalized_environment = _normalize_environment(environment)
    environment_id = _resolve_environment_id(normalized_environment)
    matching_flags = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).all()
    if not matching_flags:
        raise KeyError(flag_key)

    environment_flag = next(
        (flag for flag in matching_flags if flag.environment_id == environment_id),
        None,
    )
    baseline_flag = next(
        (flag for flag in matching_flags if flag.environment_id == 1),
        None,
    )
    resolved_flag = environment_flag or baseline_flag or matching_flags[0]
    effective_config = _resolve_environment_config(db, resolved_flag, normalized_environment)
    configured_value = effective_config["default_value"]

    def result(value: Any, source: str) -> dict[str, Any]:
        return {
            "flag_key": resolved_flag.key,
            "value": value,
            "source": source,
            "environment": normalized_environment,
        }

    target_users = effective_config["target_users"] or []
    if user_id in target_users:
        return result(configured_value if effective_config["enabled"] else False, "user_targeting")

    target_groups = effective_config["target_groups"] or []
    user_groups = {
        membership.group_name
        for membership in db.query(UserGroupMembership).filter(UserGroupMembership.user_id == user_id).all()
    }
    if (group and group in target_groups) or user_groups.intersection(target_groups):
        return result(configured_value if effective_config["enabled"] else False, "group_targeting")

    if evaluate_percentage_rollout(user_id, resolved_flag.key, int(effective_config["rollout_percentage"] or 0)):
        return result(configured_value if effective_config["enabled"] else False, "percentage_rollout")

    environment_record = db.query(Environment).filter(Environment.key == normalized_environment).first()
    has_environment_override = environment_record is not None and db.query(FlagEnvironmentOverride).filter(
        FlagEnvironmentOverride.flag_id == resolved_flag.id,
        FlagEnvironmentOverride.environment_id == environment_id,
    ).first() is not None
    if has_environment_override:
        return result(configured_value if effective_config["enabled"] else False, "environment_override")

    return result(configured_value if effective_config["enabled"] else False, "default")


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

    effective_config = _resolve_environment_config(db, resolved_flag, environment)

    resolved = {
        "key": resolved_flag.key,
        "environment": _normalize_environment(environment),
        "enabled": bool(effective_config["enabled"]),
        "default_value": effective_config["default_value"],
        "reason": None,
    }

    if not effective_config["enabled"]:
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

    ctx = user_context or {}

    target_users = effective_config["target_users"] or []
    user_id = ctx.get("user_id")
    if user_id is not None and user_id in target_users:
        resolved["enabled"] = True
        resolved["reason"] = "user_targeted"
        return resolved

    target_groups = effective_config["target_groups"] or []
    if user_id is not None and target_groups:
        memberships = db.query(UserGroupMembership).filter(UserGroupMembership.user_id == user_id).all()
        user_groups = [m.group_name for m in memberships]
        if any(g in target_groups for g in user_groups):
            resolved["enabled"] = True
            resolved["reason"] = "group_targeted"
            return resolved

    if user_id is not None:
        rollout_percentage = int(effective_config["rollout_percentage"] or 0)
        enabled_for_rollout = evaluate_percentage_rollout(user_id, resolved_flag.key, rollout_percentage)
        if enabled_for_rollout:
            resolved["enabled"] = bool(effective_config["enabled"])
            resolved["reason"] = "default"
        else:
            resolved["enabled"] = False
            resolved["reason"] = "rollout"

    resolved["reason"] = resolved.get("reason") or "default"
    if include_reason:
        return resolved

    return {
        "key": resolved["key"],
        "environment": resolved["environment"],
        "enabled": resolved["enabled"],
        "default_value": resolved["default_value"],
    }
