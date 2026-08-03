from fastapi.testclient import TestClient

from app.main import app, init_db
from app.database import SessionLocal
from app.schemas import FlagCreate
from app.crud import create_flag
from app.models import UserGroupMembership, FeatureFlag


def test_group_targeting_evaluation():
    # Ensure fresh schema
    init_db()

    client = TestClient(app)

    db = SessionLocal()

    # Create a flag that targets group 'beta'
    flag_payload = {
        "key": "group-test-flag",
        "type": "boolean",
        "default_value": False,
        "enabled": True,
        "description": "Group targeting test",
        "owner_team": "qa",
        "environment_id": 2,
        "target_users": [],
        "target_groups": ["beta"],
    }

    flag_obj = FlagCreate(**flag_payload)
    create_flag(db, flag_obj)

    # Add a membership for user 'user-42' -> 'beta'
    m = UserGroupMembership(user_id="user-42", group_name="beta")
    db.add(m)
    db.commit()

    # Evaluate via test client endpoint
    resp = client.get(
        "/evaluate",
        params={"key": "group-test-flag", "environment": "staging", "user_id": "user-42"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert data["reason"] == "group_targeted"

    # If user explicitly targeted, user takes precedence
    flag = db.query(FeatureFlag).filter_by(key="group-test-flag").first()
    flag.target_users = ["user-42"]
    db.commit()

    resp2 = client.get(
        "/evaluate",
        params={"key": "group-test-flag", "environment": "staging", "user_id": "user-42"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["enabled"] is True
    assert data2["reason"] == "user_targeted"
