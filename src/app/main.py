from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from src.app.api.router import api_router
from src.app.core.database import get_engine, Base
from src.app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and apply any missing column migrations safely."""
    logger.info("Starting AI Lead Qualifier v2...")
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)

        with engine.begin() as conn:
            # Safe idempotent migrations — won't fail if column already exists
            migrations = [
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS title VARCHAR;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS address VARCHAR;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_reason TEXT;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS website VARCHAR;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS website_summary TEXT;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS apollo_enriched BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS outreach_sent BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS outreach_channel VARCHAR;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;",
            ]
            for sql in migrations:
                conn.execute(text(sql))
            logger.info(f"Schema verified: {len(migrations)} migrations checked.")

    except Exception as e:
        logger.error(f"Startup schema migration failed: {e}")

    yield
    logger.info("Shutting down AI Lead Qualifier.")


app = FastAPI(
    title="AI Lead Qualifier API",
    version="2.0.0",
    description=(
        "Production-grade AI lead generation: "
        "Google Maps + Apollo scraping → Tavily enrichment → Gemini AI scoring → WhatsApp/Email outreach"
    ),
    lifespan=lifespan,
)

# CORS — allows the frontend (browser) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten to your S3/domain URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
