from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.cache import invalidate_all_evaluation_cache, invalidate_flag_evaluation_cache
from app.models import Environment, FeatureFlag, FlagEnvironmentOverride
from app.schemas import EnvironmentCreate, EnvironmentUpdate, FlagCreate, FlagUpdate


def create_flag(db: Session, flag: FlagCreate) -> FeatureFlag:
    """Create a new feature flag record in the database.

    This function validates that the incoming key is unique within the same
    environment before persisting the ORM object.
    """

    existing_flag = (
        db.query(FeatureFlag)
        .filter(FeatureFlag.key == flag.key, FeatureFlag.environment_id == flag.environment_id)
        .first()
    )
    if existing_flag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feature flag with key '{flag.key}' already exists for environment '{flag.environment_id}'.",
        )

    db_flag = FeatureFlag(
        key=flag.key,
        type=flag.type.value,
        default_value=flag.default_value,
        enabled=flag.enabled,
        rollout_percentage=flag.rollout_percentage,
        target_users=flag.target_users,
        target_groups=flag.target_groups,
        description=flag.description,
        owner_team=flag.owner_team,
        environment_id=flag.environment_id,
    )

    db.add(db_flag)
    db.commit()
    db.refresh(db_flag)
    invalidate_flag_evaluation_cache(db_flag.key)
    return db_flag


def get_flags(db: Session) -> list[FeatureFlag]:
    """Return all feature flags from the database."""

    return db.query(FeatureFlag).order_by(FeatureFlag.environment_id, FeatureFlag.key).all()


def get_flag_by_key(db: Session, key: str) -> FeatureFlag:
    """Fetch a single feature flag by its key.

    The API currently exposes a single-record detail view for the requested
    key. If multiple environment variants exist, the first matching record is
    returned in deterministic order.
    """

    db_flag = db.query(FeatureFlag).filter(FeatureFlag.key == key).order_by(FeatureFlag.environment_id).first()
    if not db_flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' was not found.",
        )

    return db_flag


def update_flag(db: Session, key: str, flag: FlagUpdate) -> FeatureFlag:
    """Update an existing feature flag record.

    The function first loads the record by its unique key. If the update payload
    includes a new key value, the function checks whether that new key is already
    assigned to another record and raises a 409 Conflict if it is.
    """

    db_flag = db.query(FeatureFlag).filter(FeatureFlag.key == key).first()
    if not db_flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' was not found.",
        )

    previous_key = db_flag.key
    if flag.key and flag.key != db_flag.key:
        target_environment_id = flag.environment_id if flag.environment_id is not None else db_flag.environment_id
        duplicate_check = (
            db.query(FeatureFlag)
            .filter(FeatureFlag.key == flag.key, FeatureFlag.environment_id == target_environment_id)
            .first()
        )
        if duplicate_check and duplicate_check.id != db_flag.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Feature flag with key '{flag.key}' already exists for environment "
                    f"'{target_environment_id}'."
                ),
            )

    if flag.key is not None:
        db_flag.key = flag.key
    if flag.type is not None:
        db_flag.type = flag.type.value
    if flag.default_value is not None:
        db_flag.default_value = flag.default_value
    if flag.enabled is not None:
        db_flag.enabled = flag.enabled
    if flag.rollout_percentage is not None:
        db_flag.rollout_percentage = flag.rollout_percentage
    if flag.target_users is not None:
        db_flag.target_users = flag.target_users
    if flag.target_groups is not None:
        db_flag.target_groups = flag.target_groups
    if flag.description is not None:
        db_flag.description = flag.description
    if flag.owner_team is not None:
        db_flag.owner_team = flag.owner_team
    if flag.environment_id is not None:
        db_flag.environment_id = flag.environment_id

    db.commit()
    invalidate_flag_evaluation_cache(previous_key)
    if db_flag.key != previous_key:
        invalidate_flag_evaluation_cache(db_flag.key)
    db.refresh(db_flag)
    return db_flag


def delete_flag(db: Session, key: str) -> None:
    """Remove feature flag records by key.

    The endpoint deletes all records that match the requested key since the
    application stores environment-specific overrides under the same key.
    """

    deleted_count = db.query(FeatureFlag).filter(FeatureFlag.key == key).delete(synchronize_session=False)
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' was not found.",
        )

    db.commit()
    invalidate_flag_evaluation_cache(key)


def list_environments(db: Session) -> list[Environment]:
    """Return all configured environments."""

    return db.query(Environment).order_by(Environment.id).all()


def create_environment(db: Session, environment: EnvironmentCreate) -> Environment:
    """Create a new environment record if the key is not already used."""

    existing = db.query(Environment).filter(Environment.key == environment.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Environment with key '{environment.key}' already exists.",
        )

    db_environment = Environment(
        name=environment.name,
        key=environment.key,
        description=environment.description,
    )
    db.add(db_environment)
    db.commit()
    db.refresh(db_environment)
    invalidate_all_evaluation_cache()
    return db_environment


def update_environment(db: Session, environment_id: int, environment: EnvironmentUpdate) -> Environment:
    """Update an existing environment record."""

    db_environment = db.query(Environment).filter(Environment.id == environment_id).first()
    if not db_environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_id}' was not found.",
        )

    if environment.key is not None and environment.key != db_environment.key:
        duplicate = db.query(Environment).filter(Environment.key == environment.key).first()
        if duplicate and duplicate.id != db_environment.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment with key '{environment.key}' already exists.",
            )

    if environment.name is not None:
        db_environment.name = environment.name
    if environment.key is not None:
        db_environment.key = environment.key
    if environment.description is not None:
        db_environment.description = environment.description

    db.commit()
    db.refresh(db_environment)
    return db_environment


def get_environment_by_id(db: Session, environment_id: int) -> Environment:
    """Return a single environment by id."""

    db_environment = db.query(Environment).filter(Environment.id == environment_id).first()
    if not db_environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_id}' was not found.",
        )
    return db_environment


def get_flag_environment_overrides(db: Session, flag_key: str) -> list[FlagEnvironmentOverride]:
    """Return all override records for a feature flag."""

    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).order_by(FeatureFlag.environment_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{flag_key}' was not found.",
        )

    return db.query(FlagEnvironmentOverride).filter(FlagEnvironmentOverride.flag_id == flag.id).all()


def get_or_create_flag_environment_override(db: Session, flag_key: str, environment_id: int, payload: dict | None = None):
    """Create or update a flag override for a flag and environment."""

    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).order_by(FeatureFlag.environment_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{flag_key}' was not found.",
        )

    environment = db.query(Environment).filter(Environment.id == environment_id).first()
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_id}' was not found.",
        )

    override = (
        db.query(FlagEnvironmentOverride)
        .filter(FlagEnvironmentOverride.flag_id == flag.id, FlagEnvironmentOverride.environment_id == environment.id)
        .first()
    )

    if override is None:
        override = FlagEnvironmentOverride(
            flag_id=flag.id,
            environment_id=environment.id,
            enabled=True,
            default_value=flag.default_value,
            rollout_percentage=flag.rollout_percentage,
            target_users=flag.target_users or [],
            target_groups=flag.target_groups or [],
            description=None,
        )
        db.add(override)

    if payload:
        if "enabled" in payload and payload["enabled"] is not None:
            override.enabled = payload["enabled"]
        if "default_value" in payload and payload["default_value"] is not None:
            override.default_value = payload["default_value"]
        if "rollout_percentage" in payload and payload["rollout_percentage"] is not None:
            override.rollout_percentage = payload["rollout_percentage"]
        if "target_users" in payload and payload["target_users"] is not None:
            override.target_users = payload["target_users"]
        if "target_groups" in payload and payload["target_groups"] is not None:
            override.target_groups = payload["target_groups"]
        if "description" in payload and payload["description"] is not None:
            override.description = payload["description"]

    db.commit()
    db.refresh(override)
    invalidate_flag_evaluation_cache(flag.key)
    return override
