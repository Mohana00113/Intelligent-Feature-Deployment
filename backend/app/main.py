from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.cache import evaluation_cache
from app.engine import evaluate_feature_flag, evaluate_feature_flag_request
from app.routes.environments import router as environments_router
from app.routes.flag_environment_overrides import router as flag_environment_overrides_router
from app.routes.flags import router as flags_router
from app.schemas import FlagEvaluationRequest, FlagEvaluationResponse, RuntimeFlagEvaluationResponse

app = FastAPI(title="Intelligent Feature Deployment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(flags_router, prefix="/flags", tags=["Feature Flags"])
app.include_router(environments_router, prefix="/environments", tags=["Environments"])
app.include_router(flag_environment_overrides_router, prefix="/flag-environment-overrides", tags=["Flag Environment Overrides"])


@app.on_event("startup")
def startup_event() -> None:
    """Ensure the database schema is created before processing requests."""

    init_db()


# Create the DB at import time as well to support test clients that import the
# app module without triggering lifespan handlers in some test runners.
try:
    init_db()
except Exception:
    # Avoid raising during import if the DB can't be created in the current environment.
    pass


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Intelligent Feature Deployment API is running"}


@app.get(
    "/evaluate",
    response_model=FlagEvaluationResponse,
    summary="Evaluate a feature flag for an environment",
)
def evaluate_flag(
    key: str,
    environment: str,
    user_id: str | None = None,
    db: Session = Depends(get_db),
) -> FlagEvaluationResponse:
    """Resolve a feature flag's enabled state for an environment."""

    try:
        user_context = {"user_id": user_id} if user_id is not None else None
        return evaluate_feature_flag(db=db, key=key, environment=environment, user_context=user_context, include_reason=True)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' was not found.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post(
    "/evaluate",
    response_model=RuntimeFlagEvaluationResponse,
    summary="Evaluate a feature flag for a runtime user",
)
def evaluate_runtime_flag(
    request: FlagEvaluationRequest,
    db: Session = Depends(get_db),
) -> RuntimeFlagEvaluationResponse:
    """Resolve a feature flag using targeting, rollout, and fallback rules."""

    try:
        cached_result = evaluation_cache.get(request.flag_key, request.environment, request.user_id, request.group)
        if cached_result is not None:
            return {**cached_result, "cached": True}

        result = evaluate_feature_flag_request(
            db=db,
            flag_key=request.flag_key,
            environment=request.environment,
            user_id=request.user_id,
            group=request.group,
        )
        evaluation_cache.set(
            request.flag_key,
            request.environment,
            request.user_id,
            request.group,
            result,
        )
        return {**result, "cached": False}
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{request.flag_key}' was not found.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
