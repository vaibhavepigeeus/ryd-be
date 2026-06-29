import imaplib
import email
import smtplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

from decouple import config

EMAIL_USER = config("IMAP_EMAIL_USER", default=config("EMAIL_HOST_USER", default=""))
EMAIL_PASS = config("IMAP_EMAIL_PASS", default=config("SMTP_PASSWORD", default=""))
IMAP_SERVER = config("IMAP_SERVER", default="imap.gmail.com")
IMAP_PORT = config("IMAP_PORT", default=993, cast=int)
SMTP_SERVER = config("SMTP_SERVER", default=config("EMAIL_HOST", default="smtp.gmail.com"))
SMTP_PORT = config("SMTP_PORT", default=587, cast=int)


def clean_subject(subject):
    if subject:
        subject, encoding = decode_header(subject)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
    return subject


def read_emails(from_date_str=None, to_date_str=None, from_name=None):
    from datetime import datetime as dt

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        search_criteria = "ALL"
        if from_date_str or to_date_str:
            date_criteria = []

            def try_parse_date(s):
                if not s:
                    return None
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        return dt.strptime(s, fmt)
                    except Exception:
                        continue
                return None

            if from_date_str:
                from_date = try_parse_date(from_date_str)
                if from_date:
                    date_criteria.append(f"SINCE {from_date.strftime('%d-%b-%Y')}")
            if to_date_str:
                to_date = try_parse_date(to_date_str)
                if to_date:
                    imap_before = (to_date + timedelta(days=1)).strftime("%d-%b-%Y")
                    date_criteria.append(f"BEFORE {imap_before}")
            if date_criteria:
                search_criteria = " ".join(date_criteria)

        status, messages = mail.search(None, search_criteria)
        email_ids = messages[0].split() if messages and messages[0] else []
        output = []

        for eid in email_ids[-1:-26:-1]:
            msg_id = int(eid)
            status, msg_data = mail.fetch(eid, "(RFC822)")
            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue
                msg = email.message_from_bytes(response_part[1])
                subject = clean_subject(msg["subject"])
                from_full = msg.get("from")
                if from_full and "<" in from_full:
                    from_name_only = from_full.split("<")[0].strip()
                else:
                    from_name_only = from_full

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                dt_parsed = parsedate_to_datetime(msg["Date"])
                formatted_date = dt_parsed.strftime("%d-%m-%Y %H:%M")

                should_include = True
                if from_name:
                    if not from_name_only or from_name.lower() not in from_name_only.lower():
                        should_include = False

                if should_include:
                    output.append({
                        "id": msg_id,
                        "from": from_name_only,
                        "from_full_name": from_full,
                        "to": EMAIL_USER,
                        "subject": subject,
                        "body": body,
                        "date": formatted_date,
                    })

        mail.logout()
        return output
    except Exception:
        return []


def send_email(data):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = data["from"]
    msg["Subject"] = data["subject"]
    msg.attach(MIMEText(data["reply"], "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, data["from"], msg.as_string())

    return {"message": "Email sent successfully"}
