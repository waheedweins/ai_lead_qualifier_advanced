import logging
from src.app.services.langgraph_engine import lead_scoring_graph

logger = logging.getLogger("lead-engine.ai-service")


class AIService:
    def score_lead(self, lead: dict) -> dict:
        """
        Score a lead via LangGraph (Tavily enrichment → Gemini scoring).
        Always returns a safe dict even on failure.
        """
        if lead_scoring_graph is None:
            logger.error("LangGraph not initialized — returning default score.")
            return {"score": 0, "decision": "cold", "reason": "AI scoring unavailable"}

        try:
            result = lead_scoring_graph.invoke({
                "lead": lead,
                "score": 0,
                "query": "",
                "results": [],
                "decision": "",
                "reason": "",
                "website_summary": "",
            })
            return {
                "score": result.get("score", 0),
                "decision": result.get("decision", "cold"),
                "reason": result.get("reason", ""),
            }
        except Exception as e:
            logger.error(f"AI scoring failed for {lead.get('email')}: {e}")
            return {"score": 0, "decision": "cold", "reason": f"Error: {e}"}
