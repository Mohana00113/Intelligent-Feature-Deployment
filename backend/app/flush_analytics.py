"""Daily job entry point: run with `python -m app.flush_analytics`."""

from app.analytics import flush_evaluation_counts
from app.cache import evaluation_cache
from app.database import SessionLocal


def main() -> None:
    with SessionLocal() as db:
        flushed = flush_evaluation_counts(db, evaluation_cache.client)
    print(f"Flushed {flushed} evaluation metric bucket(s).")


if __name__ == "__main__":
    main()