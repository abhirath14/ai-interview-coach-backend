import logging
import time
from typing import Optional

from groq import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    Groq,
    InternalServerError,
    RateLimitError,
)

from .config import GROQ_API_KEY

logger = logging.getLogger("ai_interview_coach")

client = Groq(api_key=GROQ_API_KEY)

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 0.6


def _is_retryable(error: Exception) -> bool:
    if isinstance(
        error, (RateLimitError, InternalServerError, APIConnectionError, APITimeoutError)
    ):
        return True
    if isinstance(error, BadRequestError):
        # Groq occasionally fails to produce schema-conformant JSON on the
        # first attempt even in strict structured-output mode. Retrying the
        # same request usually succeeds.
        return "json_validate_failed" in str(error)
    return False


def create_completion(**kwargs):
    """Wraps client.chat.completions.create with retries for transient Groq failures."""
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as error:
            last_error = error
            if attempt < MAX_ATTEMPTS and _is_retryable(error):
                logger.warning(
                    "Groq call failed (attempt %d/%d), retrying: %s",
                    attempt,
                    MAX_ATTEMPTS,
                    error,
                )
                time.sleep(RETRY_DELAY_SECONDS * attempt)
                continue
            raise

    raise last_error
