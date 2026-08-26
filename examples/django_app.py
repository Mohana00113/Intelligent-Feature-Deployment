import atexit
import os

from django.http import JsonResponse

from backend.app.feature_flag_client import FeatureFlagClient

flags = FeatureFlagClient(os.getenv("FEATURE_FLAG_API_URL", "http://127.0.0.1:8000"), refresh_interval=30)
flags.start()
atexit.register(flags.stop)


class FlagClientMiddleware:
    """Expose the shared feature flag client on each Django request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.feature_flags = flags
        return self.get_response(request)


def checkout(request):
    return JsonResponse({"new_checkout": request.feature_flags.is_enabled("new_checkout")})