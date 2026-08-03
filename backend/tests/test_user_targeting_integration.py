from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db, SessionLocal, engine
from app.models import Base, FeatureFlag


def setup_module(module):
    # Ensure fresh schema for this integration test
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)


def test_evaluate_endpoint_user_targeting():
    client = TestClient(app)

    # Create a flag that targets a specific user
    session = SessionLocal()
    try:
        f = FeatureFlag(
            key="integration_whitelist",
            type="boolean",
            default_value=False,
            enabled=True,
            description="integration test whitelist",
            owner_team="Platform",
            environment_id=1,
            target_users=["user-in-1"],
        )
        session.add(f)
        session.commit()

        # 1) targeted user -> enabled=true, reason=user_targeted
        resp = client.get(
            "/evaluate",
            params={"key": "integration_whitelist", "environment": "development", "user_id": "user-in-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("enabled") is True
        assert body.get("reason") == "user_targeted"

        # 2) non-targeted user -> normal/default behavior
        resp2 = client.get(
            "/evaluate",
            params={"key": "integration_whitelist", "environment": "development", "user_id": "someone-else"},
        )
        assert resp2.status_code == 200
        body2 = resp2.json()
        # The flag is enabled and not user-targeted, the engine should return reason 'default'
        assert body2.get("enabled") is True
        assert body2.get("reason") in ("default", None)

    finally:
        try:
            # clean up the created record so other tests run against an empty DB
            session.query(FeatureFlag).filter(FeatureFlag.key == "integration_whitelist").delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
