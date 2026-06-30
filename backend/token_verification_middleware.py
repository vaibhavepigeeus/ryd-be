import json
import logging
from enum import Enum

from django.http import JsonResponse
from knox.models import AuthToken
from helpers.azure_token_helper import (
    decode_azure_token,
    generate_azure_token,
)
from knox.auth import TokenAuthentication
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from users.models import *
from users.utils import send_email
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)


def clean_cookie_token(value):
    """Strip accidental suffixes (e.g. ' : username') from cookie token values."""
    if not value:
        return None
    token = str(value).strip()
    if " " in token:
        token = token.split()[0]
    return token or None


class TokenVerificationMiddleware:
    """
    Middleware for token verification and user audit data logging.

    - Handles exemption paths for specific API endpoints.
    - Verifies JWT tokens for authentication.
    - Saves user audit data to a model or logs it (implementation choice).
    - Provides flexibility for customizing logging behavior (levels, formats).
    """

    def __init__(self, get_response):
        self.routes_to_exclude = [
            "/admin",
            "/static/",
            "/media/",
            "/api/users/login",
            "/api/users/register/",
            "/api/users/forgot-password/",
            "/api/users/token/refresh/",
            "/api/users/check-user/",
            "/api/users/verify-otp/",
            "/api/users/create-password/",
            "/api/users/oauth_login/",
            "/api/users/logout/",
        ]

        self.get_response = get_response
        self.token_authentication = TokenAuthentication()

    def __call__(self, request):
        # Read and store the request body at the beginning
        logger.info("TokenVerificationMiddleware called")
        try:
            request_body = request.body.decode("utf-8")
        except Exception:
            request_body = ""

        # Check if the request path starts with /api/users/login or /api/users/forgot-password/
        if any(request.path.startswith(route) for route in self.routes_to_exclude):
            # If it does, skip token authentication and proceed with the request
            return self.get_response(request)

        # Allow form builder API access in local development
        if settings.DEBUG and request.path.startswith("/api/forms/"):
            return self.get_response(request)

        # Allow document uploads for the form builder in local development
        if settings.DEBUG and request.path.startswith("/api/documents/"):
            return self.get_response(request)

        # Extract the token
        logger.info("Cookies: %s", request.COOKIES)
        refresh_token = clean_cookie_token(request.COOKIES.get("refreshToken"))
        access_token = clean_cookie_token(request.COOKIES.get("accessToken"))
        login_method = request.COOKIES.get("loginMethod")
        user_id = request.COOKIES.get("userId")

        if not refresh_token and not access_token:
            logger.info("No token found in cookies....session expired")
            response = self.get_response(request)
            for cookie in request.COOKIES:
                response.delete_cookie(cookie)

            return JsonResponse(
                {"message": "Session expired. Please login again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            if not user_id:
                return JsonResponse(
                    {"message": "Session expired. Please login again."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return JsonResponse(
                    {"message": "User not found. Please login again."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not validate_session(user=user):
                logger.info("Session doesn't exists for user.")
                return JsonResponse(
                    {"message": "Session doesn't exists. Please login again."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            refreshed_access_token = None

            if login_method == LoginMethods.BASIC.value:
                if not access_token and refresh_token:
                    user, _ = self.token_authentication.authenticate_credentials(
                        refresh_token.encode()
                    )
                    user = Users.objects.get(pk=user.pk)
                    _, refreshed_access_token = AuthToken.objects.create(user)
                    access_token = refreshed_access_token
                elif access_token:
                    user, _ = self.token_authentication.authenticate_credentials(
                        access_token.encode()
                    )
                else:
                    return JsonResponse(
                        {"message": "Session expired. Please login again."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

            elif login_method == LoginMethods.OAUTH.value:
                try:
                    decode_azure_token(access_token=access_token)
                except Exception as e:
                    if "expired" in str(e).lower() and refresh_token:
                        token_response = generate_azure_token(
                            authorization_code=None,
                            refresh_token=refresh_token,
                        )
                        refreshed_access_token = token_response.get("access_token")
                        access_token = refreshed_access_token
                    else:
                        raise
            else:
                return JsonResponse(
                    {"error": "Invalid Login Method"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            request.user = user
            request.META["HTTP_X-user"] = user

            response = self.get_response(request)

            if refreshed_access_token:
                response.set_cookie(
                    key="accessToken",
                    value=refreshed_access_token,
                    httponly=True,
                    secure=settings.SESSION_COOKIE_SECURE,
                    samesite="Lax",
                    max_age=24 * 60 * 60,
                )

            save_audit_data(
                user,
                request,
                response.status_code,
                payload=request_body,
                response_data=response.content,
            )

            return response

        except AuthenticationFailed as e:
            response = JsonResponse(
                {"message": str(e), "error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            save_audit_data(
                None,
                request,
                response.status_code,
                payload=request_body,
                response_data=response.content,
            )
            logger.error("Authentication failed for the request: %s", request.path)
            return response
        except Exception:
            logger.exception("Unhandled error in token middleware for: %s", request.path)
            raise


def validate_session(user):
    """
    Function to check if the provided token exists and is valid for the given user.
    """
    try:
        # Retrieve the user's token information from the UserSessionManagement table
        user_token = UserSessionManagement.objects.filter(user=user).first()

        # Check if the user has a token entry
        if not user_token:
            return False

        # Check if the provided token matches the stored access token
        if user_token.isLoggedIn:
            return True

        return False
    except Exception as e:
        # In case of any error, consider the token invalid
        logger.error("Token validation failed: %s", str(e))
        return False


# Optional function for saving to UserAuditHistory model (replace with your logic)
def save_audit_data(user, request, status_code, payload=None, response_data=None):
    """
    Function to save Audit Data to UserAuditHistory model
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0]  # Get the first IP
    else:
        # Fallback to REMOTE_ADDR if X-Forwarded-For is not available
        ip_address = request.META.get("REMOTE_ADDR")

    # Handle payload
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="replace")
    try:
        payload_json = json.loads(payload)
    except json.JSONDecodeError:
        payload_json = payload  # Keep as string if not valid JSON

    # Handle response
    if isinstance(response_data, bytes):
        response_data = response_data.decode("utf-8", errors="replace")
    elif hasattr(response_data, "content"):
        response_data = response_data.content
        if isinstance(response_data, bytes):
            response_data = response_data.decode("utf-8", errors="replace")

    try:
        response_json = json.loads(response_data)
    except (json.JSONDecodeError, TypeError):
        response_json = response_data  # Keep as string if not valid JSON or not a

    # Handle response
    if hasattr(response_data, "content"):
        response_content = response_data.content
        if isinstance(response_content, bytes):
            response_content = response_content.decode("utf-8", errors="replace")
    else:
        response_content = str(response_data)

    try:
        response_json = json.loads(response_content)
    except json.JSONDecodeError:
        response_json = response_content

    try:
        audit_data = {
            "user": user,
            "ip": ip_address,
            "api_url": request.path,
            "api_method": request.method,
            "response_status_code": status_code,
        }

        if request.method != "GET":
            audit_data["payload"] = payload_json
            audit_data["response"] = response_json

        audit_history = UserAuditHistory.objects.create(**audit_data)
        body_contenet = f"""
            API failed with {status_code} error.
            audit_id: {audit_history.id}
            audit_data: {audit_data}
            \n\n Env: {settings.ENVIRONMENT}
        """
        env = config("ENVIRONMENT", default="DEVELOPMENT")
        if status_code not in [200, 201, 401, 404] and env == "PRODUCTION":
            send_email(
                sender_email="cmtadmin@mosaicfintech.com",
                recipient_email=[
                    "kumars@epigeeus.com",
                    "shivali.goel@mosaicinsurance.com",
                ],
                subject="API failed",
                body=body_contenet,
            )
        logger.info(
            f"Audit data saved successfully for user: {user.id if user else 'Anonymous'}"
        )
    except Exception as e:
        logger.error(f"Error saving audit data: {str(e)}")


def validate_token(user, token):
    """
    Function to check if the provided token exists and is valid for the given user.
    """
    try:
        # Retrieve the user's token information from the UserSessionManagement table
        user_token = UserSessionManagement.objects.filter(user=user).first()

        # Check if the user has a token entry
        if not user_token:
            return False

        # Check if the provided token matches the stored access token
        if user_token.access_token == token:
            return True

        return False
    except Exception as e:
        # In case of any error, consider the token invalid
        logger.error("Token validation failed: %s", str(e))
        return False


class LoginMethods(Enum):
    """
    Enum for login methods
    """

    BASIC = "BASIC"
    OAUTH = "OAUTH"
