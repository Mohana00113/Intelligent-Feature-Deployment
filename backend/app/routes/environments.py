from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import create_environment, get_environment_by_id, list_environments, update_environment
from app.database import get_db
from app.models import Environment
from app.schemas import EnvironmentCreate, EnvironmentResponse, EnvironmentUpdate

router = APIRouter(tags=["Environments"])


@router.get("", response_model=list[EnvironmentResponse], summary="List environments")
def list_feature_environments(db: Session = Depends(get_db)) -> list[Environment]:
    return list_environments(db=db)


@router.post("", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED, summary="Create environment")
def create_feature_environment(environment: EnvironmentCreate, db: Session = Depends(get_db)) -> Environment:
    return create_environment(db=db, environment=environment)


@router.put("/{environment_id}", response_model=EnvironmentResponse, summary="Update environment")
def update_feature_environment(
    environment_id: int,
    environment: EnvironmentUpdate,
    db: Session = Depends(get_db),
) -> Environment:
    return update_environment(db=db, environment_id=environment_id, environment=environment)


@router.get("/{environment_id}", response_model=EnvironmentResponse, summary="Fetch environment by id")
def get_feature_environment(environment_id: int, db: Session = Depends(get_db)) -> Environment:
    return get_environment_by_id(db=db, environment_id=environment_id)
