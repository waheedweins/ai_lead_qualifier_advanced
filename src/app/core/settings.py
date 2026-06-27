import json
import logging
import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

logger = logging.getLogger("lead-engine")


def fetch_aws_secrets() -> dict:
    """Fetch secrets from AWS Secrets Manager. Falls back gracefully for local dev."""
    secret_name = "production/LeadQualifier"
    region_name = "eu-north-1"
    try:
        client = boto3.client("secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response["SecretString"])
        logger.info("AWS Secrets loaded successfully.")
        return secrets
    except Exception as e:
        logger.warning(f"AWS Secrets unavailable (local dev mode): {e}")
        return {}


AWS_SECRETS = fetch_aws_secrets()


class Settings(BaseSettings):
    APP_NAME: str = "AI Lead Engine"
    DEBUG: bool = False
    ENV: str = "production"

    # Database
    DATABASE_URL: str | None = AWS_SECRETS.get("DATABASE_URL")

    # Scrapers
    APIFY_API_TOKEN: str | None = AWS_SECRETS.get("APIFY_API_TOKEN")
    APOLLO_API_KEY: str | None = AWS_SECRETS.get("APOLLO_API_KEY")

    # AI
    GEMINI_API_KEY: str | None = AWS_SECRETS.get("GEMINI_API_KEY")
    TAVILY_API_KEY: str | None = AWS_SECRETS.get("TAVILY_API_KEY")

    # Outreach
    SENDGRID_API_KEY: str | None = AWS_SECRETS.get("SENDGRID_API_KEY")
    EMAIL_FROM: str | None = AWS_SECRETS.get("EMAIL_FROM")
    WHATSAPP_TOKEN: str | None = AWS_SECRETS.get("WHATSAPP_TOKEN")
    WHATSAPP_PHONE_ID: str | None = AWS_SECRETS.get("WHATSAPP_PHONE_ID")

    # AWS
    AWS_REGION: str = "eu-north-1"
    AWS_SECRET_NAME: str = "production/LeadQualifier"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        import os
        # Fallback to .env / environment variables for local development
        if not self.DATABASE_URL:
            self.DATABASE_URL = os.getenv("DATABASE_URL")
        if not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.TAVILY_API_KEY:
            self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        if not self.APIFY_API_TOKEN:
            self.APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
        if not self.APOLLO_API_KEY:
            self.APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

        logger.info(f"DATABASE_URL     : {'✓' if self.DATABASE_URL else '✗ MISSING'}")
        logger.info(f"GEMINI_API_KEY   : {'✓' if self.GEMINI_API_KEY else '✗ missing (heuristic fallback)'}")
        logger.info(f"TAVILY_API_KEY   : {'✓' if self.TAVILY_API_KEY else '✗ missing (skipping enrichment)'}")
        logger.info(f"APIFY_API_TOKEN  : {'✓' if self.APIFY_API_TOKEN else '✗ missing'}")
        logger.info(f"APOLLO_API_KEY   : {'✓' if self.APOLLO_API_KEY else '✗ missing (Apollo disabled)'}")
        logger.info(f"SENDGRID_API_KEY : {'✓' if self.SENDGRID_API_KEY else '✗ missing (email disabled)'}")
        logger.info(f"WHATSAPP_TOKEN   : {'✓' if self.WHATSAPP_TOKEN else '✗ missing (WhatsApp disabled)'}")

        if not self.DATABASE_URL:
            raise ValueError("CRITICAL: DATABASE_URL is missing. Cannot start.")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
