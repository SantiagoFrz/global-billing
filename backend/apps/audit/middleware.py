from .context import request_ip, request_user


class AuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_token = request_user.set(
            request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        )
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip_token = request_ip.set(
            (forwarded.split(",")[0] if forwarded else request.META.get("REMOTE_ADDR")) or None
        )
        try:
            return self.get_response(request)
        finally:
            request_user.reset(user_token)
            request_ip.reset(ip_token)
