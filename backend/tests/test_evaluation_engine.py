import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.engine import evaluate_feature_flag, evaluate_percentage_rollout
from app.models import Base, FeatureFlag, UserGroupMembership


@pytest.fixture()
def db_session():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_returns_default_value_when_no_rule_matches(db_session):
    default_flag = FeatureFlag(
        key="new_dashboard",
        type="boolean",
        default_value=True,
        enabled=True,
        description="default flag",
        owner_team="Platform",
        environment_id=1,
    )

    db_session.add(default_flag)
    db_session.commit()

    result = evaluate_feature_flag(db_session, "new_dashboard", "staging")

    assert result["key"] == "new_dashboard"
    assert result["environment"] == "staging"
    assert result["enabled"] is True
    assert result["default_value"] is True


def test_environment_override_has_priority_over_default(db_session):
    production_flag = FeatureFlag(
        key="new_dashboard",
        type="boolean",
        default_value=False,
        enabled=False,
        description="production override",
        owner_team="Platform",
        environment_id=3,
    )
    default_flag = FeatureFlag(
        key="new_dashboard",
        type="boolean",
        default_value=True,
        enabled=True,
        description="default flag",
        owner_team="Platform",
        environment_id=1,
    )

    db_session.add(production_flag)
    db_session.add(default_flag)
    db_session.commit()

    result = evaluate_feature_flag(db_session, "new_dashboard", "production")

    assert result["key"] == "new_dashboard"
    assert result["environment"] == "production"
    assert result["enabled"] is False
    assert result["default_value"] is False


def test_disabled_flag_returns_false_and_keeps_default_value(db_session):
    default_flag = FeatureFlag(
        key="beta_feature",
        type="boolean",
        default_value=True,
        enabled=False,
        description="feature is disabled",
        owner_team="Platform",
        environment_id=1,
    )

    db_session.add(default_flag)
    db_session.commit()

    result = evaluate_feature_flag(db_session, "beta_feature", "development")

    assert result["enabled"] is False
    assert result["default_value"] is True


def test_missing_or_empty_user_context_is_handled_safely(db_session):
    default_flag = FeatureFlag(
        key="new_dashboard",
        type="boolean",
        default_value=True,
        enabled=True,
        description="default flag",
        owner_team="Platform",
        environment_id=1,
    )

    db_session.add(default_flag)
    db_session.commit()

    result_without_context = evaluate_feature_flag(db_session, "new_dashboard", "staging")
    result_with_empty_context = evaluate_feature_flag(db_session, "new_dashboard", "staging", user_context={})

    assert result_without_context["enabled"] is True
    assert result_without_context["default_value"] is True
    assert result_with_empty_context["enabled"] is True
    assert result_with_empty_context["default_value"] is True


def test_user_in_target_users_is_enabled_immediately(db_session):
    default_flag = FeatureFlag(
        key="whitelist_feature",
        type="boolean",
        default_value=False,
        enabled=True,
        description="user whitelist",
        owner_team="Platform",
        environment_id=1,
        target_users=["user-42"],
    )

    db_session.add(default_flag)
    db_session.commit()

    result = evaluate_feature_flag(
        db_session, "whitelist_feature", "development", user_context={"user_id": "user-42"}, include_reason=True
    )

    assert result["enabled"] is True
    assert result["default_value"] is False
    assert result["reason"] == "user_targeted"


def test_rollout_percentage_zero_disables_everyone(db_session):
    flag = FeatureFlag(
        key="percentage_zero",
        type="boolean",
        default_value=True,
        enabled=True,
        description="test rollout",
        owner_team="Platform",
        environment_id=1,
        rollout_percentage=0,
    )
    db_session.add(flag)
    db_session.commit()

    for user_id in ["user-1", "user-2", "user-3"]:
        result = evaluate_feature_flag(
            db_session,
            "percentage_zero",
            "development",
            user_context={"user_id": user_id},
            include_reason=True,
        )
        assert result["enabled"] is False
        assert result["reason"] == "rollout"


def test_rollout_percentage_hundred_enables_everyone(db_session):
    flag = FeatureFlag(
        key="percentage_hundred",
        type="boolean",
        default_value=False,
        enabled=True,
        description="test rollout",
        owner_team="Platform",
        environment_id=1,
        rollout_percentage=100,
    )
    db_session.add(flag)
    db_session.commit()

    for user_id in ["user-1", "user-2", "user-3"]:
        result = evaluate_feature_flag(
            db_session,
            "percentage_hundred",
            "development",
            user_context={"user_id": user_id},
            include_reason=True,
        )
        assert result["enabled"] is True
        assert result["reason"] in {"default", "rollout"}


def test_rollout_is_deterministic_for_same_user_and_flag():
    first = evaluate_percentage_rollout("user-42", "beta_flag", 25)
    second = evaluate_percentage_rollout("user-42", "beta_flag", 25)
    third = evaluate_percentage_rollout("user-42", "beta_flag", 25)

    assert first == second == third


def test_rollout_can_split_users_and_flags_into_different_buckets():
    bucket_a = evaluate_percentage_rollout("user-1", "flag-a", 50)
    bucket_b = evaluate_percentage_rollout("user-2", "flag-a", 50)
    bucket_c = evaluate_percentage_rollout("user-1", "flag-b", 50)

    assert bucket_a in {True, False}
    assert bucket_b in {True, False}
    assert bucket_c in {True, False}
    assert bucket_a == evaluate_percentage_rollout("user-1", "flag-a", 50)
    assert bucket_b != bucket_c or bucket_a == bucket_c


def test_invalid_rollout_percentage_values_are_rejected():
    with pytest.raises(ValueError):
        evaluate_percentage_rollout("user-1", "flag-a", -1)

    with pytest.raises(ValueError):
        evaluate_percentage_rollout("user-1", "flag-a", 101)


def test_group_targeting_still_works_when_rollout_is_configured(db_session):
    flag = FeatureFlag(
        key="rollout_group_flag",
        type="boolean",
        default_value=False,
        enabled=True,
        description="rollout plus group targeting",
        owner_team="Platform",
        environment_id=1,
        rollout_percentage=0,
        target_groups=["beta"],
    )
    db_session.add(flag)
    db_session.add(UserGroupMembership(user_id="user-42", group_name="beta"))
    db_session.commit()

    result = evaluate_feature_flag(
        db_session,
        "rollout_group_flag",
        "development",
        user_context={"user_id": "user-42"},
        include_reason=True,
    )

    assert result["enabled"] is True
    assert result["reason"] == "group_targeted"
