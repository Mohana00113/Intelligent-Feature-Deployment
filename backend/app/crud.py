from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import FeatureFlag
from app.schemas import FlagCreate, FlagUpdate


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
        description=flag.description,
        owner_team=flag.owner_team,
        environment_id=flag.environment_id,
    )

    db.add(db_flag)
    db.commit()
    db.refresh(db_flag)
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
    if flag.description is not None:
        db_flag.description = flag.description
    if flag.owner_team is not None:
        db_flag.owner_team = flag.owner_team
    if flag.environment_id is not None:
        db_flag.environment_id = flag.environment_id

    db.commit()
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
