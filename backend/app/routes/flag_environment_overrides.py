from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import get_flag_environment_overrides, get_or_create_flag_environment_override
from app.database import get_db
from app.models import FlagEnvironmentOverride
from app.schemas import FlagEnvironmentOverrideCreate, FlagEnvironmentOverrideResponse, FlagEnvironmentOverrideUpdate

router = APIRouter(tags=["Flag Environment Overrides"])


@router.get("", response_model=list[FlagEnvironmentOverrideResponse], summary="List environment overrides for a flag")
def list_flag_overrides(flag_key: str, db: Session = Depends(get_db)) -> list[FlagEnvironmentOverride]:
    return get_flag_environment_overrides(db=db, flag_key=flag_key)


@router.put("/{environment_id}", response_model=FlagEnvironmentOverrideResponse, summary="Upsert an environment override")
def upsert_flag_override(
    flag_key: str,
    environment_id: int,
    override: FlagEnvironmentOverrideUpdate,
    db: Session = Depends(get_db),
) -> FlagEnvironmentOverride:
    payload = override.model_dump(exclude_unset=True, exclude_none=True)
    return get_or_create_flag_environment_override(db=db, flag_key=flag_key, environment_id=environment_id, payload=payload)


@router.post("", response_model=FlagEnvironmentOverrideResponse, status_code=status.HTTP_201_CREATED, summary="Create environment override")
def create_flag_override(
    flag_key: str,
    override: FlagEnvironmentOverrideCreate,
    db: Session = Depends(get_db),
) -> FlagEnvironmentOverride:
    payload = override.model_dump(exclude_unset=True)
    return get_or_create_flag_environment_override(db=db, flag_key=flag_key, environment_id=override.environment_id, payload=payload)
