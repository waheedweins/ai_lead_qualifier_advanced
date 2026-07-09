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
    APIFY_API_KEY: str | None = None
    APOLLO_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    
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
        # AWS Secrets Manager parsing block can reside here if active
        aws_secrets = data.get("AWS_SECRETS", {})
        
        # Pull properties sequentially out of AWS Context map if present
        if aws_secrets:
            data["DATABASE_URL"] = aws_secrets.get("DATABASE_URL")
            data["GEMINI_API_KEY"] = aws_secrets.get("GEMINI_API_KEY")
            data["APIFY_API_KEY"] = aws_secrets.get("APIFY_API_KEY")
            data["APOLLO_API_KEY"] = aws_secrets.get("APOLLO_API_KEY")
            data["TAVILY_API_KEY"] = aws_secrets.get("TAVILY_API_KEY")
            data["AUTH0_DOMAIN"] = aws_secrets.get("AUTH0_DOMAIN")
            data["AUTH0_AUDIENCE"] = aws_secrets.get("AUTH0_AUDIENCE")
            
        return data

    def model_post_init(self, __context: Any) -> None:
        """
        Post-initialization validation to enforce local system .env fallbacks
        if properties were missing from the production AWS context layer.
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = os.getenv("DATABASE_URL")
        if not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.APIFY_API_KEY:
            self.APIFY_API_KEY = os.getenv("APIFY_API_KEY")
        if not self.APOLLO_API_KEY:
            self.APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
        if not self.TAVILY_API_KEY:
            self.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
            
        # Auth0 Fallback assignments
        if not self.AUTH0_DOMAIN:
            self.AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
        if not self.AUTH0_AUDIENCE:
            self.AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

        logger.info(f"System settings loaded for project: {self.PROJECT_NAME}")
        if self.AUTH0_DOMAIN:
            logger.info(f"Identity protection active for tenant domain: {self.AUTH0_DOMAIN}")
        else:
            logger.warning("Auth0 configuration missing. Active routes are unprotected.")


# Instantiate global workspace configurations settings singleton
settings = Settings()
