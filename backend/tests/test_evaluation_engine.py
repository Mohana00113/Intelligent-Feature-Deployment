import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.engine import evaluate_feature_flag
from app.models import Base, FeatureFlag


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
