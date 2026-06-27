import logging
import re
import requests
from src.app.core.settings import settings
from src.app.utils.retry import retry

logger = logging.getLogger("lead-engine.whatsapp-service")


def _format_phone(phone: str) -> str:
    """
    Normalise phone to E.164 format (digits only, leading +).
    WhatsApp API requires this format.
    """
    digits = re.sub(r"\D", "", phone)
    if not digits.startswith("92") and len(digits) == 10:
        digits = "92" + digits   # default Pakistan country code
    return digits


class WhatsAppService:
    def __init__(self):
        if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID:
            raise RuntimeError("WHATSAPP_TOKEN or WHATSAPP_PHONE_ID not configured — WhatsApp disabled.")
        self.token = settings.WHATSAPP_TOKEN
        self.phone_id = settings.WHATSAPP_PHONE_ID
        self.url = f"https://graph.facebook.com/v20.0/{self.phone_id}/messages"

    def send_message(self, phone: str, message: str) -> dict:
        formatted = _format_phone(phone)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted,
            "type": "text",
            "text": {"body": message},
        }

        def _send():
            r = requests.post(self.url, headers=headers, json=payload, timeout=10)
            r.raise_for_status()
            return r.json()

        try:
            result = retry(_send, retries=3, delay=2.0)
            logger.info(f"WhatsApp sent to {formatted}")
            return result
        except Exception as e:
            logger.error(f"WhatsApp failed to {formatted}: {e}")
            raise
