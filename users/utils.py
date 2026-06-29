import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

def send_email(sender_email, recipient_email, subject, body):
    message = MIMEMultipart()
    smtp_username = settings.SMTP_USERNAME
    smtp_password = settings.SMTP_PASSWORD
    smtp_host = settings.EMAIL_HOST
    message['From'] = sender_email
    message['To'] = recipient_email[0]
    message['Subject'] = subject
    
    message.attach(MIMEText(body, 'html'))
    with smtplib.SMTP(smtp_host, 587) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, recipient_email, message.as_string())

def get_masked_email(email):
    try:
        user_part, domain_part = email.split("@", 1)
        masked_email = f"***@{domain_part}"
    except:
        masked_email = email  # In case the email is not in standard format
    return masked_email