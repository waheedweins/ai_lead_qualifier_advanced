import logging
from apify_client import ApifyClient
from src.app.core.settings import settings
from src.app.utils.retry import retry

logger = logging.getLogger("lead-engine.scrapers.google_maps")


class GoogleMapsScraper:
    """Scrapes business leads from Google Maps via Apify."""

    ACTOR_NAME = "compass/crawler-google-places"
    ACTOR_FALLBACK = "nwua9Gu5YrADL7ZDj"

    def __init__(self):
        self.token = settings.APIFY_API_TOKEN
        self.client = ApifyClient(self.token) if self.token else None

    def scrape(self, search_query: str, max_results: int = 30) -> list[dict]:
        if not self.client:
            logger.warning("GoogleMapsScraper: APIFY_API_TOKEN missing — skipping.")
            return []

        run_input = {
            "searchStringsArray": [search_query],
            "maxCrawledPlacesPerSearch": max_results,
            "language": "en",
            "includeWebResults": True,
        }

        def _run():
            try:
                return self.client.actor(self.ACTOR_NAME).call(run_input=run_input)
            except Exception as e:
                logger.warning(f"Actor name failed, trying ID fallback: {e}")
                return self.client.actor(self.ACTOR_FALLBACK).call(run_input=run_input)

        try:
            logger.info(f"Launching Apify Google Maps for: '{search_query}'")
            run = retry(_run, retries=3, delay=3.0)
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                logger.error("No dataset ID returned from Apify.")
                return []
            items = self.client.dataset(dataset_id).list_items().items
            logger.info(f"Google Maps returned {len(items)} results for '{search_query}'")
            return items
        except Exception as e:
            logger.error(f"Google Maps scraping failed for '{search_query}': {e}")
            return []
