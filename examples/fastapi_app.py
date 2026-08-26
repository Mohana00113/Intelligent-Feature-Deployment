from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.feature_flag_client import FeatureFlagClient

flags = FeatureFlagClient("http://127.0.0.1:8000", refresh_interval=30)


@asynccontextmanager
async def lifespan(_: FastAPI):
    flags.start()
    try:
        yield
    finally:
        flags.stop()


app = FastAPI(title="Feature Flag FastAPI Example", lifespan=lifespan)


@app.get("/checkout")
def checkout() -> dict[str, object]:
    return {"new_checkout": flags.is_enabled("new_checkout")}