import logging
from sqlalchemy.orm import Session
from src.app.crud.lead import (
    create_lead, get_lead_by_email, get_leads,
    get_lead_by_id, update_lead_score, update_lead_enrichment,
    get_lead_stats, mark_lead_failed, clear_all_leads,
)
from src.app.schemas.lead import LeadCreate
from src.app.services.ai_service import AIService

logger = logging.getLogger("lead-engine.lead-service")


class LeadService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService()

    def list_all(self, skip: int = 0, limit: int = 100):
        return get_leads(self.db, skip=skip, limit=limit)

    def get_by_id(self, lead_id: int):
        return get_lead_by_id(self.db, lead_id)

    def stats(self) -> dict:
        return get_lead_stats(self.db)

    def clear_all_leads(self) -> int:
        return clear_all_leads(self.db)

    def create(self, lead: LeadCreate):
        """
        Creates a lead in DB, optionally enriches via Apollo,
        then runs Gemini AI scoring.
        """
        existing = get_lead_by_email(self.db, email=lead.email)
        if existing:
            logger.debug(f"Lead already exists: {lead.email}")
            return existing

        new_lead = create_lead(db=self.db, lead=lead)

        # Apollo enrichment (runs only if Apollo key is configured)
        self._try_apollo_enrich(new_lead)

        # AI scoring
        try:
            lead_dict = new_lead.__dict__.copy()
            lead_dict.pop("_sa_instance_state", None)

            result = self.ai.score_lead(lead_dict)
            update_lead_score(
                db=self.db,
                lead=new_lead,
                score=result.get("score", 0),
                reason=result.get("reason", ""),
            )
            logger.info(
                f"Lead {new_lead.id} ({new_lead.email}) scored "
                f"{result['score']} ({result['decision']}): {result.get('reason', '')}"
            )
        except Exception as e:
            logger.warning(f"AI scoring failed for lead {new_lead.id}: {e}")

        return new_lead

    def rescore(self, lead_id: int) -> dict | None:
        """Re-run AI scoring on an existing lead."""
        lead = get_lead_by_id(self.db, lead_id)
        if not lead:
            return None

        lead_dict = lead.__dict__.copy()
        lead_dict.pop("_sa_instance_state", None)

        result = self.ai.score_lead(lead_dict)
        update_lead_score(
            db=self.db,
            lead=lead,
            score=result.get("score", 0),
            reason=result.get("reason", ""),
        )
        return {
            "id": lead.id,
            "email": lead.email,
            "ai_score": lead.ai_score,
            "ai_reason": lead.ai_reason,
            "decision": result.get("decision", "cold"),
        }

    def _try_apollo_enrich(self, lead) -> None:
        """
        Attempt Apollo enrichment to fill in missing phone/website/title.
        Runs silently — never crashes the main flow.
        """
        try:
            from src.app.scrapers.apollo_scraper import ApolloScraper
            apollo = ApolloScraper()
            if not apollo.enabled:
                return

            enriched = apollo.enrich_lead(lead.email)
            if enriched:
                update_lead_enrichment(
                    db=self.db,
                    lead=lead,
                    website=enriched.get("website"),
                    phone=enriched.get("phone"),
                    apollo_enriched=True,
                )
                logger.info(f"Apollo enriched lead {lead.id} ({lead.email})")
        except Exception as e:
            logger.debug(f"Apollo enrichment skipped for {lead.email}: {e}")
