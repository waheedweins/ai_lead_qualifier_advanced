from sqlalchemy.orm import Session
from sqlalchemy import func
from src.app.models.lead import Lead
from src.app.schemas.lead import LeadCreate


def create_lead(db: Session, lead: LeadCreate) -> Lead:
    db_lead = Lead(
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        title=lead.title,
        address=lead.address,
        website=lead.website,
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


def get_lead_by_email(db: Session, email: str) -> Lead | None:
    return db.query(Lead).filter(Lead.email == email).first()


def get_lead_by_phone(db: Session, phone: str) -> Lead | None:
    return db.query(Lead).filter(Lead.phone == phone).first()


def get_lead_by_id(db: Session, lead_id: int) -> Lead | None:
    return db.query(Lead).filter(Lead.id == lead_id).first()


def get_leads(db: Session, skip: int = 0, limit: int = 100) -> list[Lead]:
    return db.query(Lead).order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()


def update_lead_score(db: Session, lead: Lead, score: int, reason: str) -> Lead:
    lead.ai_score = score
    lead.ai_reason = reason
    db.commit()
    db.refresh(lead)
    return lead


def update_lead_enrichment(
    db: Session,
    lead: Lead,
    website: str | None = None,
    website_summary: str | None = None,
    phone: str | None = None,
    apollo_enriched: bool = False,
) -> Lead:
    if website:
        lead.website = website
    if website_summary:
        lead.website_summary = website_summary
    if phone and not lead.phone:
        lead.phone = phone
    lead.apollo_enriched = apollo_enriched
    db.commit()
    db.refresh(lead)
    return lead


def mark_outreach_sent(db: Session, lead: Lead, channel: str) -> Lead:
    lead.outreach_sent = True
    lead.outreach_channel = channel
    lead.status = "processed"
    db.commit()
    db.refresh(lead)
    return lead


def mark_lead_failed(db: Session, lead: Lead) -> Lead:
    lead.status = "failed"
    db.commit()
    db.refresh(lead)
    return lead


def clear_all_leads(db: Session) -> int:
    """Delete every lead (and cascaded agent_runs). Returns count of rows deleted."""
    num_deleted = db.query(Lead).delete()
    db.commit()
    return num_deleted


def get_lead_stats(db: Session) -> dict:
    total = db.query(func.count(Lead.id)).scalar() or 0
    hot = db.query(func.count(Lead.id)).filter(Lead.ai_score >= 50).scalar() or 0
    avg_score = db.query(func.avg(Lead.ai_score)).scalar() or 0.0
    processed = db.query(func.count(Lead.id)).filter(Lead.status == "processed").scalar() or 0
    new_leads = db.query(func.count(Lead.id)).filter(Lead.status == "new").scalar() or 0
    outreach_sent = db.query(func.count(Lead.id)).filter(Lead.outreach_sent == True).scalar() or 0
    apollo_enriched = db.query(func.count(Lead.id)).filter(Lead.apollo_enriched == True).scalar() or 0
    return {
        "total": total,
        "hot": hot,
        "cold": total - hot,
        "avg_score": round(float(avg_score), 1),
        "processed": processed,
        "new_leads": new_leads,
        "outreach_sent": outreach_sent,
        "apollo_enriched": apollo_enriched,
    }
