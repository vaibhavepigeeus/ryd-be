from knox.auth import TokenAuthentication

from backend.token_verification_middleware import clean_cookie_token
from users.models import Users


def get_user_from_request(request):
    user = getattr(request, "user", None)
    if user and isinstance(user, Users):
        return user

    user_id = request.COOKIES.get("userId")
    if user_id:
        try:
            return Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            pass

    access_token = clean_cookie_token(request.COOKIES.get("accessToken"))
    if access_token:
        try:
            token_user, _ = TokenAuthentication().authenticate_credentials(
                access_token.encode(),
            )
            return Users.objects.get(pk=token_user.pk)
        except Exception:
            pass

    return None
