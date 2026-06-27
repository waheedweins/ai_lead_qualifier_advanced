from fastapi import APIRouter
from src.app.api.v1.lead_routes import router as lead_router
from src.app.api.v1.scrape_routes import router as scrape_router
from src.app.api.v1.health_routes import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(lead_router)
api_router.include_router(scrape_router)
