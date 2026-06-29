"""
Django settings for RYD backend project.
"""

from datetime import timedelta
from pathlib import Path

from corsheaders.defaults import default_headers
from decouple import config
from rest_framework.settings import api_settings

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-ryd-dev-key-change-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "documents",
    "filemanagement",
    "workflow",
    "audit",
    "forms",
    "rest_framework",
    "corsheaders",
    "django_otp.plugins.otp_totp",
    "knox",
    "django_filters",
    "storages",
    "channels",
]

ASGI_APPLICATION = "backend.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(config("REDIS_HOST", default="127.0.0.1"), config("REDIS_PORT", default=6379, cast=int))],
        },
    },
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "backend.custom_middleware_validation.NotFoundMiddleware",
    "backend.token_verification_middleware.TokenVerificationMiddleware",
    "backend.custom_middleware_validation.SpecialCharacterMiddleware",
    "backend.custom_middleware_validation.DecodeURLEncodedMiddleware",
    "backend.custom_middleware_validation.CustomMiddleware",
]

ROOT_URLCONF = "backend.urls"

SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_USER_MODEL = "users.Users"
WSGI_APPLICATION = "backend.wsgi.application"

EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_USE_SSL = False
SMTP_USERNAME = config("SMTP_USERNAME", default="")
SMTP_PASSWORD = config("SMTP_PASSWORD", default="")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("DATABASE_NAME", default="ryd_db"),
        "USER": config("DATABASE_USER", default="postgres"),
        "PASSWORD": config("DATABASE_PASSWORD", default="postgres"),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

USE_S3 = config("USE_S3", default=False, cast=bool)

if USE_S3:
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = None
    AWS_S3_SECURE_URLS = False
    DEFAULT_FILE_STORAGE = "backend.storage_backends.MediaStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_HEADERS = list(default_headers) + ["login-method", "user-id", "referer"]

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": ("knox.auth.TokenAuthentication",),
}

REST_KNOX = {
    "SECURE_HASH_ALGORITHM": "hashlib.sha512",
    "AUTH_TOKEN_CHARACTER_LENGTH": 64,
    "TOKEN_TTL": timedelta(minutes=60),
    "USER_SERIALIZER": "knox.serializers.UserSerializer",
    "TOKEN_LIMIT_PER_USER": None,
    "AUTO_REFRESH": True,
    "EXPIRY_DATETIME_FORMAT": api_settings.DATETIME_FORMAT,
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config("ALLOWED_ORIGINS", default="http://localhost:5173").split(",")
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")

ENVIRONMENT = config("ENVIRONMENT", default="DEVELOPMENT")

WORK_FLOW_INITIATE_BODY = """
<html><body>
<p>Dear {reviewer_approver},</p>
<p>A new worklist item {transaction_id} has been assigned to you, initiated by {initiator}. Please review it as soon as possible.</p>
<p>ENV: {env_name}</p>
</body></html>
"""

WORK_FLOW_CHANGE_STATUS_BODY = """
<html><body>
<p>Dear {initiator},</p>
<p>The worklist item {transaction_id} has been {status} by {reviewer_approver}.</p>
<p>ENV: {env_name}</p>
</body></html>
"""

WORK_FLOW_CHANGE_STATUS_REVIEWER_BODY = """
<html><body>
<p>Dear {reviewer_approver},</p>
<p>A new worklist item {transaction_id} has been assigned to you, initiated by {initiator}. Please review it as soon as possible.</p>
<p>ENV: {env_name}</p>
</body></html>
"""

WORK_FLOW_CHANGE_STATUS_CONFIRMATION_BODY = """
<html><body>
<p>Dear {reviewer_approver},</p>
<p>Status of {transaction_id} is changed. No further action from your end is required.</p>
<p>ENV: {env_name}</p>
</body></html>
"""

USER_ONBOARD = """
<html><body>
<p>Dear User,</p>
<p>Welcome! Your one-time password: <strong>{password}</strong></p>
<p>ENV: {env_name}</p>
</body></html>
"""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
