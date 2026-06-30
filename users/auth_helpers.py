from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from documents.utils.encryption_util import decrypt_text
from knox.models import AuthToken

from backend.token_verification_middleware import LoginMethods
from .models import UserSessionManagement, Users


def find_user_by_email(email: str, require_active: bool = True) -> Users | None:
    target_email = email.lower()

    base_query = Users.objects
    if require_active:
        base_query = base_query.filter(status="Active")

    user = base_query.filter(email__iexact=target_email).first()

    if not user:
        users_to_check = base_query.only("id", "email", "status", "user_name")
        for user_obj in users_to_check:
            try:
                decrypted_email = decrypt_text(user_obj.email)
                if decrypted_email.lower() == target_email:
                    return user_obj
            except Exception:
                continue

    return user


def set_auth_cookies(response, user):
    _, access_token = AuthToken.objects.create(
        user=user,
        expiry=timedelta(hours=1),
    )
    _, refresh_token = AuthToken.objects.create(
        user=user,
        expiry=timedelta(days=1),
    )

    cookie_secure = settings.SESSION_COOKIE_SECURE
    max_age = 24 * 60 * 60
    cookie_map = {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "userId": user.id,
        "loginMethod": LoginMethods.BASIC.value,
    }

    for key, value in cookie_map.items():
        response.set_cookie(
            key=key,
            value=str(value),
            httponly=True,
            secure=cookie_secure,
            samesite="Lax",
            max_age=max_age,
        )

    UserSessionManagement.objects.update_or_create(
        user=user,
        defaults={
            "logged_in_time": timezone.now(),
            "isLoggedIn": True,
        },
    )

    return access_token, refresh_token


def build_user_payload(user):
    return {
        "id": user.id,
        "user_name": user.user_name,
        "email": user.get_decrypted_email(),
        "role": user.role,
        "status": user.status,
        "coach_id": user.reporting_manager_id,
        "coach_name": user.reporting_manager.user_name if user.reporting_manager else None,
    }
