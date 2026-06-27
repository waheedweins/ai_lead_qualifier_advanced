import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from src.app.core.settings import settings
from src.app.utils.retry import retry

logger = logging.getLogger("lead-engine.email-service")


class EmailService:
    def __init__(self):
        if not settings.SENDGRID_API_KEY:
            raise RuntimeError("SENDGRID_API_KEY not configured — email disabled.")
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def send_email(self, recipient: str, subject: str, content: str, html_content: str | None = None) -> int:
        if not settings.EMAIL_FROM:
            raise RuntimeError("EMAIL_FROM not configured.")

        message = Mail(
            from_email=settings.EMAIL_FROM,
            to_emails=recipient,
            subject=subject,
            plain_text_content=content,
            html_content=html_content or content,
        )

        def _send():
            response = self.client.send(message)
            logger.info(f"Email sent to {recipient}: HTTP {response.status_code}")
            return response.status_code

        return retry(_send, retries=3, delay=2.0)
