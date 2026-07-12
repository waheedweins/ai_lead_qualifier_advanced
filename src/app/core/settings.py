import logging
import os
from typing import Any, Dict
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setup logger configuration
logger = logging.getLogger("app_settings")
logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    # Base Configurations
    PROJECT_NAME: str = "Mission Impossible AI Lead Qualifier"
    API_V1_STR: str = "/api/v1"
    
    # AWS Secrets Container Fallback Dict
    AWS_SECRETS: Dict[str, Any] = {}

    # Target Structural Database Configurations
    DATABASE_URL: str | None = None
    
    # Core API Keys and Routing Tolerances
    GEMINI_API_KEY: str | None = None
    APIFY_API_TOKEN: str | None = None
    APOLLO_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None

    # Outreach Channel Credentials
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str | None = None
    WHATSAPP_TOKEN: str | None = None
    WHATSAPP_PHONE_ID: str | None = None

    # Auth0 Security Parameters
    AUTH0_DOMAIN: str | None = None
    AUTH0_AUDIENCE: str | None = None

    # Load configuration settings from local workspace environment files
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    @model_validator(mode="before")
    @classmethod
    def pre_load_settings(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-load hook to check for live AWS Secrets Manager values
        before parsing variables into configuration properties.
        """
        aws_secrets = data.get("AWS_SECRETS", {})
        
        if aws_secrets:
            data["DATABASE_URL"] = aws_secrets.get("DATABASE_URL")
            data["GEMINI_API_KEY"] = aws_secrets.get("GEMINI_API_KEY")
            data["APIFY_API_TOKEN"] = aws_secrets.get("APIFY_API_TOKEN")
            data["APOLLO_API_KEY"] = aws_secrets.get("APOLLO_API_KEY")
            data["TAVILY_API_KEY"] = aws_secrets.get("TAVILY_API_KEY")
            data["SENDGRID_API_KEY"] = aws_secrets.get("SENDGRID_API_KEY")
            data["EMAIL_FROM"] = aws_secrets.get("EMAIL_FROM")
            data["WHATSAPP_TOKEN"] = aws_secrets.get("WHATSAPP_TOKEN")
            data["WHATSAPP_PHONE_ID"] = aws_secrets.get("WHATSAPP_PHONE_ID")
            data["AUTH0_DOMAIN"] = aws_secrets.get("AUTH0_DOMAIN")
            data["AUTH0_AUDIENCE"] = aws_secrets.get("AUTH0_AUDIENCE")
            
        return data

    def model_post_init(self, __context: Any) -> None:
        """
        Post-initialization validation to enforce local system .env fallbacks
        and hardcoded defaults if variables are missing, empty, or string "None".
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = os.getenv("DATABASE_URL")
        if not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.APIFY_API_TOKEN:
            self.APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
        if not self.APOLLO_API_KEY:
            self.APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
        if not self.TAVILY_API_KEY:
            self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        if not self.SENDGRID_API_KEY:
            self.SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
        if not self.EMAIL_FROM:
            self.EMAIL_FROM = os.getenv("EMAIL_FROM")
        if not self.WHATSAPP_TOKEN:
            self.WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
        if not self.WHATSAPP_PHONE_ID:
            self.WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
            
        # 🛡️ Robust Auth0 Fallbacks (Cleans up spaces and "None" strings)
        if not self.AUTH0_DOMAIN or str(self.AUTH0_DOMAIN).strip() in ("", "None"):
            self.AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN") or "dev-jtsob5hrzmyn2s2t.us.auth0.com"
            
        if not self.AUTH0_AUDIENCE or str(self.AUTH0_AUDIENCE).strip() in ("", "None"):
            self.AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE") or "https://dev-jtsob5hrzmyn2s2t.us.auth0.com/api/v2/"

        logger.info(f"System settings loaded for project: {self.PROJECT_NAME}")
        if self.AUTH0_DOMAIN and str(self.AUTH0_DOMAIN).strip() != "None":
            logger.info(f"Identity protection active for tenant domain: {self.AUTH0_DOMAIN}")
        else:
            logger.warning("Auth0 configuration missing. Active routes are unprotected.")


# Instantiate global workspace configurations settings singleton
settings = Settings()
