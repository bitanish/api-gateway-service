import time, math
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class TokenBucketRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = self._get_authenticated_user(request)
        if user is None:
            return self.get_response(request)

        path = request.path
        rate_config = settings.RATE_LIMITS
        path_config = rate_config.get("paths", {}).get(path, {})

        capacity = path_config.get("tokens", rate_config["default_tokens"])
        refill_rate = path_config.get("refill_rate", rate_config["default_refill_rate"])

        user_key = f"rate-limit:{user.id}:{path}"
        current_time = time.time()

        # Get token bucket from Redis
        bucket = cache.get(user_key)
        if bucket:
            tokens, last_time = bucket
        else:
            tokens = capacity
            last_time = current_time

        # Refill logic
        elapsed = current_time - last_time
        refill = elapsed * refill_rate
        tokens = min(capacity, tokens + refill)
        last_time = current_time

        if tokens >= 1:
            tokens -= 1
            cache.set(user_key, (tokens, last_time), timeout=60)

            response = self.get_response(request)

            # ✅ Add rate-limiting headers
            response["X-RateLimit-Limit"] = str(capacity)
            response["X-RateLimit-Remaining"] = str(math.floor(tokens))
            time_until_reset = math.ceil((1 - tokens) / refill_rate) if tokens < 1 else 0
            response["X-RateLimit-Reset"] = str(time_until_reset)

            return response
        else:
            return JsonResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status=429
            )

    def _get_authenticated_user(self, request):
        try:
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                return user
            else:
                auth = JWTAuthentication()
                validated = auth.authenticate(request)
                if validated is not None:
                    user, _ = validated
                    request.user = user
                    return user
        except Exception:
            pass
        return None
