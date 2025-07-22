import time
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication

class TokenBucketRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # Rate limit policy
        self.capacity = 10            # max requests
        self.refill_rate = 1         # tokens per second (~60/min)

    def __call__(self, request):
        user = self._get_authenticated_user(request)
        if user is None:
            return self.get_response(request)

        user_key = f"rate-limit:{user.id}"
        current_time = time.time()

        # Get bucket from Redis
        bucket = cache.get(user_key)
        if bucket:
            tokens, last_time = bucket
        else:
            tokens = self.capacity
            last_time = current_time

        # Refill tokens
        elapsed = current_time - last_time
        refill = elapsed * self.refill_rate
        tokens = min(self.capacity, tokens + refill)
        last_time = current_time

        if tokens >= 1:
            tokens -= 1
            cache.set(user_key, (tokens, last_time), timeout=60)
            return self.get_response(request)
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
                # Try authenticating manually if not already done
                auth = JWTAuthentication()
                validated = auth.authenticate(request)
                if validated is not None:
                    user, _ = validated
                    request.user = user
                    return user
        except Exception:
            pass
        return None
