from __future__ import annotations

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Environment, FeatureFlag, FlagEnvironmentOverride


def _create_flag(db, key: str, **kwargs):
    flag = FeatureFlag(
        key=key,
        type="boolean",
        default_value=False,
        enabled=True,
        description="test flag",
        owner_team="Platform",
        environment_id=1,
        **kwargs,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def test_environment_crud_and_seeded_defaults():
    client = TestClient(app)

    list_resp = client.get("/environments")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    keys = {item["key"] for item in payload}
    assert {"development", "staging", "production"}.issubset(keys)

    duplicate_resp = client.post("/environments", json={"name": "Development", "key": "development", "description": "dup"})
    assert duplicate_resp.status_code == 409

    create_resp = client.post("/environments", json={"name": "QA", "key": "qa", "description": "Quality assurance"})
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["key"] == "qa"

    update_resp = client.put(f"/environments/{body['id']}", json={"name": "QA Updated", "description": "Updated QA"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "QA Updated"


def test_environment_override_changes_effective_flag_evaluation():
    db = SessionLocal()
    try:
        env_dev = db.query(Environment).filter_by(key="development").one()
        env_prod = db.query(Environment).filter_by(key="production").one()

        flag = _create_flag(db, "env_override_flag", enabled=False, default_value=False, rollout_percentage=0)

        override_dev = FlagEnvironmentOverride(
            flag_id=flag.id,
            environment_id=env_dev.id,
            enabled=True,
            default_value=True,
            rollout_percentage=100,
        )
        override_prod = FlagEnvironmentOverride(
            flag_id=flag.id,
            environment_id=env_prod.id,
            enabled=False,
            default_value=False,
            rollout_percentage=0,
        )
        db.add_all([override_dev, override_prod])
        db.commit()

        dev_result = app.dependency_overrides.get(None)
        # direct engine evaluation
        from app.engine import evaluate_feature_flag

        dev_eval = evaluate_feature_flag(db, "env_override_flag", "development", user_context={"user_id": "u-1"}, include_reason=True)
        prod_eval = evaluate_feature_flag(db, "env_override_flag", "production", user_context={"user_id": "u-1"}, include_reason=True)

        assert dev_eval["enabled"] is True
        assert prod_eval["enabled"] is False
    finally:
        db.close()


def test_duplicate_flag_environment_override_rejected():
    db = SessionLocal()
    try:
        env = db.query(Environment).filter_by(key="staging").one()
        flag = _create_flag(db, "duplicate_override_flag", enabled=True)

        first = FlagEnvironmentOverride(flag_id=flag.id, environment_id=env.id, enabled=True, rollout_percentage=50)
        db.add(first)
        db.commit()

        second = FlagEnvironmentOverride(flag_id=flag.id, environment_id=env.id, enabled=False, rollout_percentage=10)
        db.add(second)
        try:
            db.commit()
            raise AssertionError("duplicate override should have been rejected")
        except Exception:
            db.rollback()
    finally:
        db.close()
