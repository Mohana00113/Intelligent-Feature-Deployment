from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.engine import evaluate_feature_flag
from app.routes.flags import router as flags_router
from app.schemas import FlagEvaluationResponse

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


@app.on_event("startup")
def startup_event() -> None:
    """Ensure the database schema is created before processing requests."""

    init_db()


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Intelligent Feature Deployment API is running"}


@app.get(
    "/evaluate",
    response_model=FlagEvaluationResponse,
    summary="Evaluate a feature flag for an environment",
)
def evaluate_flag(key: str, environment: str, db: Session = Depends(get_db)) -> FlagEvaluationResponse:
    """Resolve a feature flag's enabled state for an environment."""

    try:
        return evaluate_feature_flag(db=db, key=key, environment=environment)
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
