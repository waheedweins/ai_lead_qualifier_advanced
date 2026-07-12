import logging
import requests
import traceback
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

logger = logging.getLogger("lead-engine.services.langgraph_engine")

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    lead: dict
    score: int               # last-write-wins; only "evaluate" ever sets this
    query: str
    results: List[dict]
    decision: str           # "hot" | "cold"
    reason: str             # Gemini's one-line explanation
    website_summary: str    # Tavily enrichment result


# ── Node 1: Tavily Website Enrichment ─────────────────────────────────────────
def enrich_with_tavily(state: AgentState) -> dict:
    """
    Searches the web for the business using Tavily and summarises findings.
    Gives Gemini richer context for scoring.
    Skips silently if TAVILY_API_KEY is not set.
    """
    from src.app.core.settings import settings

    lead = state.get("lead", {})
    business_name = lead.get("name", "")
    address = lead.get("address", "")
    website = lead.get("website", "")

    if not settings.TAVILY_API_KEY or not business_name:
        return {"website_summary": ""}

    try:
        query = website if website else f"{business_name} {address} business"
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
                "include_answer": True,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        parts = []
        if data.get("answer"):
            parts.append(data["answer"])
        for r in data.get("results", [])[:2]:
            if r.get("content"):
                parts.append(r["content"][:300])

        summary = " | ".join(parts)[:600]
        logger.info(f"Tavily enriched '{business_name}': {len(summary)} chars")
        return {"website_summary": summary}

    except Exception as e:
        logger.warning(f"Tavily enrichment skipped for '{business_name}': {e}")
        return {"website_summary": ""}


# ── Node 2: Gemini AI Scoring
