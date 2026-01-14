from __future__ import annotations

import re

from app.engine.state import ConversationState
from app.utils import parse_recommend_slots
from app.ux import t
from .common_rules import msg_l, detect_language_heuristic


def _ask_recommend_clarification(state: ConversationState) -> None:
    """
    Ask the user for missing recommendation constraints and end the current turn.
    """
    state.assistant_message = t(state, "recommend_clarification_prompt")
    state.next_node = "echo"
    state.pending_recommend_clarification = True


def _merge_recommend_slots(state: ConversationState, slots) -> None:
    """
    Merge newly parsed recommendation slots into state.

    `slots` is expected to expose: families, audience, min_price, max_price.
    Only non-null fields overwrite state values.
    """
    if slots.families:
        state.recommended_family = slots.families
    if slots.audience is not None:
        state.recommended_audience = slots.audience
    if slots.min_price is not None:
        state.recommended_min_price = slots.min_price
    if slots.max_price is not None:
        state.recommended_max_price = slots.max_price


def _recommend_is_still_empty(state: ConversationState) -> bool:
    """
    Returns True when the recommendation context has no usable constraints yet.
    """
    # Defensive getattr keeps this robust if state evolves across iterations.
    return (
        not (getattr(state, "recommended_family", None) or [])
        and getattr(state, "recommended_audience", None) is None
        and getattr(state, "recommended_min_price", None) is None
        and getattr(state, "recommended_max_price", None) is None
    )


def apply_recommend_heuristic(state: ConversationState) -> bool:
    """
    Recommendation routing rule.

    Triggers when:
    - the user explicitly asks for a recommendation (ES/EN), or
    - a recommendation clarification is already pending from a previous turn.

    It parses structured recommendation slots, asks for clarification if needed,
    and routes to the recommendation node once sufficient constraints exist.
    """
    text = msg_l(state)

    pending = bool(getattr(state, "pending_recommend_clarification", False))
    is_trigger = bool(re.search(r"\b(recom|recommend)\w*\b", text))

    if not pending and not is_trigger:
        return False

    detected = detect_language_heuristic(state.user_message)
    if detected:
        state.preferred_language = detected

    lang = state.preferred_language or "es"
    slots = parse_recommend_slots(state.user_message, lang=lang)
    _merge_recommend_slots(state, slots)

    if _recommend_is_still_empty(state):
        _ask_recommend_clarification(state)
        return True

    state.pending_recommend_clarification = False
    state.next_node = "recommend_product"
    return True
