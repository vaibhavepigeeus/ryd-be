import json
import logging
import re
from urllib.parse import unquote

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Single characters blocked by SpecialCharacterMiddleware (from special_chars_list).
REQUEST_BLOCKED_CHARACTERS = set('"#;=\\~<>+/^&|')

# Safe symbols for auto-generated passwords — must not contain blocked characters.
PASSWORD_ALLOWED_SPECIAL_CHARACTERS = "!@$%*()_-?"

PASSWORD_FIELD_NAMES = frozenset(
    {"password", "oldpassword", "repassword"},
)


class NotFoundMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            return JsonResponse({
                'error': 'Resource not found',
                'message': 'The requested URL path does not exist. Please check the URL and try again.',
                'status_code': 404
            }, status=404)
        return response


class SpecialCharacterMiddleware(MiddlewareMixin):
    """
    Middleware to detect and block requests containing special characters
    in query parameters and request bodies to prevent potential security risks.
    """

    # Add fields to ignore while special char check
    ignore_fields = [
        'initialState',
        'document_file',
        'fromDate',
        'toDate',
        'key',
        'authorization_code',
        *PASSWORD_FIELD_NAMES,
    ]

    special_chars_list = [
        '"',
        ";",
        "--",
        # "#",
        "=",
        "\\",
        "~",
        "<",
        ">",
        "+",
        "/",
        "^",
        "&",
        "|",
        "http",
        "https",
        "echo",
        "script"
    ]

    def check_special_chars(self, value):
        """
        Check if the given value contains any special characters.

        :param value: Input string
        :return: The special character if found, else None
        """        
        if isinstance(value, str):
            for char in self.special_chars_list:
                if char in value:
                    return char
        return None

    def special_chars_error_check(self, body_data):
        for key, value in body_data.items():
            special_char = self.check_special_chars(value)
            if special_char and key not in self.ignore_fields:
                logger.warning(
                    "Special characters detected in request body field %s",
                    key,
                )
                return JsonResponse(
                    {"error": f"Invalid character '{special_char}' detected in request body field {key}."},
                    status=400,
                )

    def process_request(self, request):
        """
        Process incoming requests to validate and block those with special characters.
        """
        if (
            request.path.startswith("/admin")
            or request.path.startswith("/static/")
            or request.path.startswith("/api/forms/")
        ):
            return None

        # Check GET parameters
        for param, value in request.GET.items():
            special_char = self.check_special_chars(str(value))
            if special_char and param not in self.ignore_fields:
                logger.warning("Special character detected in GET parameter: %s", param)
                return JsonResponse(
                    {"error": f"Invalid character '{special_char}' detected in request parameter {param}."}, status=400
                )

        # Check POST/PATCH/PUT body
        if request.method in ["POST", "PATCH", "PUT"]:
            content_type = request.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                return None

            try:
                if request.body and "application/json" in content_type:
                    body_data = json.loads(request.body)
                    if isinstance(body_data, list):
                        for row in body_data:
                            result = self.special_chars_error_check(row)
                            if result:
                                return result
                    elif isinstance(body_data, dict):
                        return self.special_chars_error_check(body_data)

            except json.JSONDecodeError:
                if "application/json" in content_type:
                    return JsonResponse(
                        {"error": "Invalid JSON in request body"}, status=400
                    )

        return None


class CustomMiddleware(MiddlewareMixin):
    """Middleware to detect and prevent SQL injection attempts."""

    EXCLUDED_FIELDS = {
        "Broker",
        "Broker_Branch",
        "bank_name",
        "Cash_Reference",
        "comment",
        "comments",
        "file",
        "initialState",
        "key",
        "authorization_code",
        "permission_key",
        *PASSWORD_FIELD_NAMES,
    }
    SQL_PATTERNS = [
        # Basic SQL commands
        r"(?:union\s+(?:all\s+)?select|insert\s+into|update\s+set|delete\s+from)\s+\w+",
        # Dangerous SQL functions
        r"(?:exec\s+(xp_|sp_|sysobjects|syscolumns)|declare\s+@|select\s+@@)",
        # Comment markers (single-line and multi-line)
        r"(?:--|#|\/*!.*?\*/)(?=\s|$)",
        # Stacked queries
        r";\s*(?:select|insert|update|delete|drop|truncate|alter)\s+",
        # Common SQL injection test strings
        r"'(?:\s+(?:xor|nand|not|select|insert|update|delete|drop|union))\s+",
        # SQL injection payload markers
        r"(?i)(%27|%23|%2F|%3B|%3D|%27|--|#)",
        # Dangerous SQL operators
        r"(?i)(%3D)[^\n]*(%27|--|%3B|;|%2F|%3D|%2B|%26)",
        # Typical SQL injection payload markers
        r"(?i)(%27|\%3D|--|\b(select|drop|insert|update|union)\b)",
        # UNION-based injection attempts
        r"(?i)\bunion\s+.*\s+select.*\bfrom\b",
        # Standalone dangerous SQL keywords
        r"(?i)\b(delete|truncate|drop|alter|create|grant|revoke|execute|exec)\b",
        # Additional dangerous SQL keywords in context
        r"(?i)\b(select|insert|update|delete|drop|truncate|alter|create|grant|revoke|execute|exec)\s+",
        # SQL injection with common operators
        r"(?i)(union|select|insert|update|delete|drop|truncate)\s+(all\s+)?(select|from|into|set|where)",
        # Dangerous SQL patterns with quotes
        r"(?i)['\"](union|select|insert|update|delete|drop|truncate)['\"]",
        # SQL injection with common delimiters
        r"(?i)[;,\s](union|select|insert|update|delete|drop|truncate)[;,\s]",
        # JavaScript injection patterns
        r"(?i)\b(onload|onfocus|onblur|onchange|onsubmit|onclick|onmouseover|onmouseout|onkeydown|onkeyup|onkeypress|autofocus)\b",
        # JavaScript alert and prompt functions
        r"(?i)\b(alert|confirm|prompt)\s*\(",
        # JavaScript eval and function constructor
        r"(?i)\b(eval|Function|setTimeout|setInterval)\s*\(",
        # JavaScript document manipulation
        r"(?i)\b(window\.|location\.|navigator\.)",
        # JavaScript script tags
        r"(?i)<script[^>]*>.*?</script>",
        r"(?i)<script[^>]*>",
        # JavaScript code injection
        r"(?i)javascript:",
        r"(?i)vbscript:",
        # JavaScript string concatenation for injection
        r"(?i)\b(unescape|escape|encodeURI|decodeURI)\s*\(",
        # JavaScript DOM manipulation
        r"(?i)\b(innerHTML|outerHTML|innerText|outerText)\s*=",
        # JavaScript URL manipulation
        r"(?i)\b(location\.href|location\.replace|location\.assign)\s*=",
    ]

    def sql_char_error_check(self, body_data):
        for key, value in body_data.items():
            if (
                key not in self.EXCLUDED_FIELDS
                and isinstance(value, str)
                and any(
                    re.search(p, value, re.IGNORECASE)
                    for p in self.SQL_PATTERNS
                )
            ):
                logger.warning(
                    "SQL Injection attempt detected in request data: %s",
                    key,
                )
                return JsonResponse(
                    {"error": "Invalid input detected."}, status=400
                )

    def process_request(self, request):
        """Validate request data against SQL injection patterns."""
        if (
            request.path.startswith("/admin")
            or request.path.startswith("/static/")
            or request.path.startswith("/api/forms/")
        ):
            return None

        print(f"API endpoint: {request.path}")

        # Check GET parameters
        for param, value in request.GET.items():
            if param not in self.EXCLUDED_FIELDS and any(
                re.search(p, value, re.IGNORECASE) for p in self.SQL_PATTERNS
            ):
                logger.warning(
                    "SQL Injection attempt detected in GET parameter: %s", param
                )
                return JsonResponse({"error": "Invalid input detected."}, status=400)

        # Check POST/PATCH/PUT body
        if request.method in ["POST", "PATCH", "PUT"]:
            content_type = request.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                return None

            try:
                if request.body and "application/json" in content_type:
                    body_data = json.loads(request.body)
                    if isinstance(body_data, list):
                        for row in body_data:
                            result = self.sql_char_error_check(row)
                            if result:
                                return result
                    elif isinstance(body_data, dict):
                        return self.sql_char_error_check(body_data)
                        
            except json.JSONDecodeError:
                return JsonResponse(
                    {"error": "Invalid JSON in request body"}, status=400
                )

        return None

    def process_exception(self, request, exception):
        """Handle exceptions and return a generic error response."""
        logger.error("Unhandled error occurred", exc_info=exception)
        return JsonResponse(
            {"success": False, "error": "Error 1001 - Please try again later or contact to admin."}, status=400
        )


class DecodeURLEncodedMiddleware(MiddlewareMixin):
    """Middleware to decode URL-encoded special characters in request data."""

    @staticmethod
    def decode_value(value):
        """Decode a single string value."""
        return unquote(value) if isinstance(value, str) else value

    def decode_object(self, obj):
        """Recursively decode values in dictionaries or lists."""
        if obj is None:
            return obj

        if isinstance(obj, list):
            return [self.decode_object(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self.decode_object(value) for key, value in obj.items()}
        return self.decode_value(obj)

    def process_request(self, request):
        """Decode special characters in request parameters and body."""
        if request.method in {"POST", "PUT", "PATCH"} and hasattr(request, "_body"):
            try:
                decoded_data = self.decode_object(
                    json.loads(request.body.decode("utf-8"))
                )
                request._body = json.dumps(decoded_data).encode("utf-8")
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON data, skip decoding
                pass

        # Handle GET request parameters
        if request.GET:
            decoded_get = request.GET.copy()
            for key, value in request.GET.items():
                if isinstance(value, str):
                    decoded_get[key] = self.decode_object(value)
            request.GET = decoded_get

        # Handle POST form data
        if request.POST:
            decoded_post = request.POST.copy()
            for key, value in request.POST.items():
                if isinstance(value, str):
                    decoded_post[key] = self.decode_object(value)
            request.POST = decoded_post

    def process_response(self, request, response):
        """
        Process the response before it is returned to the client.

        This method can be used to modify the response object or perform
        any final checks or logging before the response is sent back to the client.

        :param request: The HTTP request object.
        :param response: The HTTP response object to be processed.
        :return: The processed HTTP response object.
        """

        return response
