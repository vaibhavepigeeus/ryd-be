from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_from_cookie(scope):
    from django.contrib.auth.models import AnonymousUser
    from knox.models import AuthToken

    headers = dict(scope["headers"])
    cookie_header = headers.get(b"cookie", b"").decode()
    if not cookie_header:
        return AnonymousUser()

    cookies = dict(item.split("=", 1) for item in cookie_header.split("; ") if "=" in item)
    token = cookies.get("accessToken")
    if not token:
        return AnonymousUser()

    try:
        return AuthToken.objects.select_related("user").get(token_key=token[:8]).user
    except AuthToken.DoesNotExist:
        return AnonymousUser()


class CookieKnoxAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = await get_user_from_cookie(scope)
        return await super().__call__(scope, receive, send)
