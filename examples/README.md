# Middleware Integration Examples

These examples use the reusable client in `backend/app/feature_flag_client.py`.
Run them from the repository root with the backend API available at `http://127.0.0.1:8000`.

## FastAPI

```powershell
pip install fastapi uvicorn
uvicorn examples.fastapi_app:app --port 8010
```

Open `http://127.0.0.1:8010/checkout` to see a flag-backed response.

## Django

Install Django in the consuming application, add `examples.django_app.FlagClientMiddleware` to `MIDDLEWARE`, and set `FEATURE_FLAG_API_URL` if the API uses a different URL. The middleware starts the client once per process, exposes it as `request.feature_flags`, and stops it during process shutdown.