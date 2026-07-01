import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

from backend.custom_middleware_validation import PASSWORD_ALLOWED_SPECIAL_CHARACTERS


def generate_combination():
    lower_letters = string.ascii_lowercase
    upper_letters = string.ascii_uppercase
    rand_lower_letters = "".join(random.choices(lower_letters, k=3))
    rand_upper_letters = "".join(random.choices(upper_letters, k=3))
    total_letters = rand_lower_letters + rand_upper_letters
    return (
        total_letters
        + str(random.randint(0, 9))
        + random.choice(PASSWORD_ALLOWED_SPECIAL_CHARACTERS)
    )


def send_email(sender_email, recipient_email, subject, body):
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
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())


def send_welcome_password_email(recipient_email, password, subject=None):
    subject = subject or "Welcome – your login password"
    body = settings.USER_ONBOARD.format(
        password=password,
        env_name=settings.ENVIRONMENT,
    )
    send_email(
        sender_email=settings.EMAIL_HOST_USER,
        recipient_email=[recipient_email],
        subject=subject,
        body=body,
    )


def get_masked_email(email):
    try:
        _, domain_part = email.split("@", 1)
        masked_email = f"***@{domain_part}"
    except Exception:
        masked_email = email
    return masked_email
