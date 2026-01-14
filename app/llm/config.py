import os


def llm_enabled() -> bool:
    """
    Check whether LLM-based routing is enabled.

    Controlled via the `LLM_ROUTER_ENABLED` environment variable.
    Defaults to enabled to simplify local development.
    """
    return os.getenv("LLM_ROUTER_ENABLED", "true").lower() == "true"


def llm_min_confidence() -> float:
    """
    Minimum confidence threshold required to trust LLM-based decisions.

    Falls back to a safe default if the environment variable is missing
    or incorrectly formatted.
    """
    try:
        return float(os.getenv("LLM_MIN_CONFIDENCE", "0.6"))
    except ValueError:
        # Defensive fallback to avoid breaking routing due to misconfiguration.
        return 0.6
