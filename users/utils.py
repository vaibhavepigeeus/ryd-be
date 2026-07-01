import logging
import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

logger = logging.getLogger(__name__)


def generate_combination():
    lower_letters = string.ascii_lowercase
    upper_letters = string.ascii_uppercase
    rand_lower_letters = "".join(random.choices(lower_letters, k=3))
    rand_upper_letters = "".join(random.choices(upper_letters, k=3))
    total_letters = rand_lower_letters + rand_upper_letters
    special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", ")", "("]
    return total_letters + str(random.randint(0, 9)) + random.choice(special_chars)


def _smtp_configured():
    return bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.EMAIL_HOST)


def _log_dev_password(recipient_email, password, reason):
    if settings.DEBUG or settings.ENVIRONMENT == "DEVELOPMENT":
        logger.warning(
            "DEV welcome password for %s: %s (%s)",
            recipient_email,
            password,
            reason,
        )


def send_email(sender_email, recipient_email, subject, body):
    if not _smtp_configured():
        raise ValueError("SMTP is not configured. Set EMAIL_USER and EMAIL_PASS in .env.")

    message = MIMEMultipart()
    smtp_username = settings.SMTP_USERNAME
    smtp_password = settings.SMTP_PASSWORD
    smtp_host = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    message["From"] = sender_email
    message["To"] = recipient_email[0]
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    if settings.EMAIL_USE_SSL:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)

    try:
        if not settings.EMAIL_USE_SSL and settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(smtp_username, smtp_password)
        refused = server.sendmail(sender_email, recipient_email, message.as_string())
    finally:
        server.quit()

    if refused:
        raise smtplib.SMTPRecipientsRefused(refused)


def send_welcome_password_email(recipient_email, password, subject=None):
    sent, _error = send_welcome_password_email_safe(recipient_email, password, subject=subject)
    if not sent:
        raise RuntimeError(_error or "Failed to send welcome password email.")


def send_welcome_password_email_safe(recipient_email, password, subject=None):
    subject = subject or "Welcome – your login password"
    body = settings.USER_ONBOARD.format(
        password=password,
        env_name=settings.ENVIRONMENT,
    )

    if not _smtp_configured():
        message = "SMTP is not configured. Set EMAIL_USER and EMAIL_PASS in .env."
        logger.error(message)
        _log_dev_password(recipient_email, password, message)
        return False, message

    try:
        send_email(
            sender_email=settings.EMAIL_HOST_USER,
            recipient_email=[recipient_email],
            subject=subject,
            body=body,
        )
    except Exception as exc:
        logger.exception(
            "Failed to send welcome password email to %s via %s:%s",
            recipient_email,
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
        )
        _log_dev_password(recipient_email, password, f"email failed: {exc}")
        return False, str(exc)

    logger.info("Welcome password email sent to %s", recipient_email)
    _log_dev_password(recipient_email, password, "email sent; password also logged in development")
    return True, None


def get_masked_email(email):
    try:
        _, domain_part = email.split("@", 1)
        masked_email = f"***@{domain_part}"
    except Exception:
        masked_email = email
    return masked_email
