import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Sends email via SMTP.
    In development, just logs the email instead of sending.
    In production, connects to real SMTP server.
    """
    if settings.DEBUG:
        # In development we don't send real emails
        # Just log so you can see what would be sent
        logger.info(f"[DEV EMAIL] To: {to_email} | Subject: {subject} | Body: {body}")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email} | Subject: {subject}")

    except Exception as e:
        # Email failure must never crash the service
        # Notification is best-effort — not critical path
        logger.error(f"Failed to send email to {to_email}: {e}")