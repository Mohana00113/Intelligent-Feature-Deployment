from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import (
    create_flag,
    delete_flag,
    get_flag_by_key,
    get_flag_environment_overrides,
    get_flags,
    get_or_create_flag_environment_override,
    update_flag,
)
from app.database import get_db
from app.schemas import (
    FlagCreate,
    FlagEnvironmentOverrideResponse,
    FlagEnvironmentOverrideUpdate,
    FlagResponse,
    FlagUpdate,
)

router = APIRouter(tags=["Feature Flags"])


@router.get(
    "/{key}/environments",
    response_model=list[FlagEnvironmentOverrideResponse],
    summary="List environment overrides for a feature flag",
)
def list_feature_flag_environment_overrides(key: str, db: Session = Depends(get_db)):
    return get_flag_environment_overrides(db=db, flag_key=key)


@router.put(
    "/{key}/environments/{environment_id}",
    response_model=FlagEnvironmentOverrideResponse,
    summary="Create or update a feature flag environment override",
)
def update_feature_flag_environment_override(
    key: str,
    environment_id: int,
    override: FlagEnvironmentOverrideUpdate,
    db: Session = Depends(get_db),
    x_actor: str | None = Header(default=None),
):
    payload = override.model_dump(exclude_unset=True, exclude_none=True)
    return get_or_create_flag_environment_override(
        db=db,
        flag_key=key,
        environment_id=environment_id,
        payload=payload,
        actor=x_actor or "system",
    )


@router.post(
    "",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new feature flag",
)
def create_feature_flag(flag: FlagCreate, db: Session = Depends(get_db), x_actor: str | None = Header(default=None)) -> FlagResponse:
    """Create a new feature flag and persist it to PostgreSQL."""

    return create_flag(db=db, flag=flag, actor=x_actor or "system")


@router.get(
    "",
    response_model=list[FlagResponse],
    summary="List all feature flags",
)
def list_feature_flags(db: Session = Depends(get_db)) -> list[FlagResponse]:
    """Return all registered feature flags from the database."""

    return get_flags(db=db)


@router.get(
    "/{key}",
    response_model=FlagResponse,
    summary="Fetch a feature flag by its unique key",
)
def get_feature_flag_by_key(key: str, db: Session = Depends(get_db)) -> FlagResponse:
    """Return a single feature flag by its unique key."""

    return get_flag_by_key(db=db, key=key)


@router.put(
    "/{key}",
    response_model=FlagResponse,
    summary="Update an existing feature flag",
)
def update_feature_flag(key: str, flag: FlagUpdate, db: Session = Depends(get_db), x_actor: str | None = Header(default=None)) -> FlagResponse:
    """Update an existing feature flag record."""

    return update_flag(db=db, key=key, flag=flag, actor=x_actor or "system")


@router.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feature flag by key",
)
def delete_feature_flag(key: str, db: Session = Depends(get_db)) -> None:
    """Delete a feature flag by its unique key."""

    delete_flag(db=db, key=key)
