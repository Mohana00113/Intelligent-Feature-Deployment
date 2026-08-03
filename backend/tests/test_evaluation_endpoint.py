import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.engine import evaluate_feature_flag
from app.models import Base, FeatureFlag


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_evaluate_returns_environment_specific_override(db_session):
    db_session.add(
        FeatureFlag(
            key="new_dashboard",
            type="boolean",
            default_value=False,
            enabled=False,
            description="production override",
            owner_team="Platform",
            environment_id=3,
        )
    )
    db_session.add(
        FeatureFlag(
            key="new_dashboard",
            type="boolean",
            default_value=True,
            enabled=True,
            description="default flag",
            owner_team="Platform",
            environment_id=1,
        )
    )
    db_session.commit()

    result = evaluate_feature_flag(db_session, "new_dashboard", "production")

    assert result == {
        "key": "new_dashboard",
        "environment": "production",
        "enabled": False,
        "default_value": False,
    }
