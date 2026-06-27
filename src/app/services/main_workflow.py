import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END
from src.app.workers.scraping_worker import run_scraping_job
from src.app.workers.lead_processor import process_leads_batch

logger = logging.getLogger("lead-engine.main-workflow")


class WorkflowState(TypedDict):
    query: str
    source: str          # "google_maps" | "apollo"
    results_count: int
    processed_count: int


def scrape_and_ingest(state: WorkflowState) -> WorkflowState:
    count = run_scraping_job(query=state["query"], source=state.get("source", "google_maps"))
    state["results_count"] = count
    logger.info(f"Scrape step: {count} new leads ingested for '{state['query']}'")
    return state


def score_and_outreach(state: WorkflowState) -> WorkflowState:
    processed = process_leads_batch()
    state["processed_count"] = processed
    logger.info(f"Processing step: {processed} leads scored and actioned")
    return state


def build_graph():
    builder = StateGraph(WorkflowState)
    builder.add_node("scrape", scrape_and_ingest)
    builder.add_node("process", score_and_outreach)
    builder.set_entry_point("scrape")
    builder.add_edge("scrape", "process")
    builder.add_edge("process", END)
    return builder.compile()


workflow = build_graph()
