from __future__ import annotations

from app.engine.state import ConversationState
from .common_rules import detect_language_heuristic, explicit_language_switch


def rule_language_detection(state: ConversationState) -> bool:
    """
    Maintain `preferred_language` based on a lightweight heuristic.

    This rule updates the state but does not route to a node. Returning False
    allows subsequent rules to continue evaluating normally in the same turn.
    """
    detected = detect_language_heuristic(state.user_message)

    if state.preferred_language is None:
        state.preferred_language = detected or "es"
    elif explicit_language_switch(state.user_message):
        state.preferred_language = detected or state.preferred_language
    elif detected and detected != state.preferred_language:
        state.preferred_language = detected

    return False
