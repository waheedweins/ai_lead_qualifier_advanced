from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.lead import LeadCreate, LeadResponse, LeadScoreResponse, LeadStatsResponse
from src.app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/", response_model=LeadResponse)
def add_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """Add a single lead — auto-enriches via Apollo and scores with Gemini AI."""
    return LeadService(db).create(lead)


@router.get("/stats", response_model=LeadStatsResponse)
def lead_stats(db: Session = Depends(get_db)):
    """Dashboard stats: totals, hot/cold split, avg score, outreach counts."""
    return LeadService(db).stats()


@router.get("/", response_model=list[LeadResponse])
def list_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all leads, newest first. Supports pagination via skip/limit."""
    return LeadService(db).list_all(skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a single lead by ID."""
    lead = LeadService(db).get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/{lead_id}/score", response_model=LeadScoreResponse)
def rescore_lead(lead_id: int, db: Session = Depends(get_db)):
    """Re-run Gemini AI scoring on an existing lead."""
    result = LeadService(db).rescore(lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result
