from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio # For running database connections safely asynchronously
from src.app.api.router import api_router
from src.app.core.database import get_engine, Base
from src.app.core.logging import logger


async def run_db_migrations():
    """Executes database schema configurations in a separate background non-blocking thread worker."""
    logger.info("Verifying schema and applying background migrations...")
    try:
        # Offload structural overhead to an isolated runner execution context
        engine = get_engine()
        Base.metadata.create_all(bind=engine)

        with engine.begin() as conn:
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
            logger.info(f"Schema verification complete. {len(migrations)} migrations validated successfully.")
    except Exception as e:
        logger.error(f"Background schema migration context failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: Instantly releases execution thread so AWS ECS Health Checks pass immediately."""
    logger.info("Initializing AI Lead Qualifier Gateway Instance v2...")
    
    # Fire off migrations asynchronously so FastAPI can start accepting API traffic immediately
    asyncio.create_task(run_db_migrations())
    
    yield
    logger.info("Shutting down AI Lead Qualifier API Gateway.")


app = FastAPI(
    title="AI Lead Qualifier API",
    version="2.0.0",
    description=(
        "Production-grade AI lead generation: "
        "Google Maps + Apollo scraping → Tavily enrichment → Gemini AI scoring → WhatsApp/Email outreach"
    ),
    lifespan=lifespan,
)

# ── CORS POLICY CONFIGURATION ────────────────────────────────────────
# Clean cross-origin array configuration supporting local test profiles and production S3 containers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://ai-lead-qualifier-advanced-frontend.s3-website.eu-north-1.amazonaws.com",
        "http://ai-lead-qualifier-advanced-frontend.s3-website.eu-north-1.amazonaws.com/",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── PUBLIC MONITORING ROUTES (DO NOT LOCK WITH AUTH0) ───────────────

@app.get("/health")
def health_check():
    """
    Public connection ping endpoint. 
    Instantly returns status to clear the frontend loading loops immediately.
    """
    return {"status": "healthy", "service": "lead_generation_advanced"}

@app.get("/")
def root_index():
    return {"message": "AI Lead Qualifier FastAPI Gateway Runtime Instance Operational"}

# ── APPLICATION ROUTES ────────────────────────────────────────────────
# Auth is enforced per-route (see lead_routes.py / scrape_routes.py), not
# blanket here — this router previously carried a global Security(auth_required)
# dependency, which locked down routes documented as public (GET /leads,
# /leads/stats, /leads/{id}, and the inner /health/) and made the Docker
# HEALTHCHECK target require a JWT it can't supply. See reference doc §4.
app.include_router(api_router)
