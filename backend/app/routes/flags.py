from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import create_flag, delete_flag, get_flag_by_key, get_flags, update_flag
from app.database import get_db
from app.schemas import FlagCreate, FlagResponse, FlagUpdate

router = APIRouter(tags=["Feature Flags"])


@router.post(
    "",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new feature flag",
)
def create_feature_flag(flag: FlagCreate, db: Session = Depends(get_db)) -> FlagResponse:
    """Create a new feature flag and persist it to PostgreSQL."""

    return create_flag(db=db, flag=flag)


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
def update_feature_flag(key: str, flag: FlagUpdate, db: Session = Depends(get_db)) -> FlagResponse:
    """Update an existing feature flag record."""

    return update_flag(db=db, key=key, flag=flag)


@router.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feature flag by key",
)
def delete_feature_flag(key: str, db: Session = Depends(get_db)) -> None:
    """Delete a feature flag by its unique key."""

    delete_flag(db=db, key=key)
