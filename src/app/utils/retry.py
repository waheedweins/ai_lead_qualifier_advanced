import time
import logging

logger = logging.getLogger("lead-engine.retry")


def retry(fn, retries: int = 3, delay: float = 2.0):
    """Synchronous retry with exponential back-off."""
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt == retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
