from __future__ import annotations

import re

from app.engine.state import ConversationState, Mode
from app.graph.routing.rules import RULES
from app.graph.routing.rules.common_rules import explicit_language_switch
from app.ux import t
from app.llm.config import llm_enabled, llm_min_confidence
from app.llm.openai_router import interpret_with_openai
from app.llm.router_schema import Intent


_INTENT_TO_NODE: dict[Intent, str] = {
    Intent.SHOW_CATALOG: "show_catalog",
    Intent.SHOW_PRODUCT_DETAIL: "show_product_detail",
    Intent.ADD_TO_CART: "add_to_cart",
    Intent.REMOVE_FROM_CART: "remove_from_cart",
    Intent.VIEW_CART: "view_cart",
    Intent.CHECKOUT: "checkout_confirm",
    Intent.RECOMMEND_PRODUCT: "recommend_product",
    Intent.BULK_CART_UPDATE: "bulk_cart_update",
    Intent.END: "echo",
    Intent.UNKNOWN: "echo",
}


def _can_accept_intent(state: ConversationState, intent: Intent) -> bool:
    """
    Guardrail to prevent the LLM router from breaking mode-specific flows.
    """
    if state.should_end or state.mode == Mode.END:
        return False

    # In these modes, only allow checkout confirmation flow.
    if state.mode == Mode.CHECKOUT_CONFIRM:
        return intent in {Intent.CONFIRM_YES, Intent.CONFIRM_NO, Intent.UNKNOWN}
    if state.mode == Mode.CHECKOUT_REVIEW:
        return intent in {Intent.CONFIRM_YES, Intent.CONFIRM_NO, Intent.UNKNOWN}
    if state.mode == Mode.COLLECT_SHIPPING:
        # While the shipping popup is open, chat input should not change the flow.
        return intent in {Intent.UNKNOWN}

    return True


def interpret_user_node(state: ConversationState) -> ConversationState:
    """
    Interpret the user message and decide the next node.

    Priority order:
    1) Deterministic rules (fast, explainable, preferred)
    2) Optional LLM router (slots + intent proposal)
    3) Fallback to `echo`
    """
    if state.should_end or state.mode == Mode.END:
        return state

    # Reset per-turn outputs to ensure a clean decision for routing.
    state.assistant_message = ""
    state.ui_products = []
    state.ui_product = None
    state.ui_cart_total = None
    state.next_node = None

    # 1) Deterministic rules drive routing when possible.
    for rule in RULES:
        if rule(state):
            return state

    # 2) Optional LLM router for intent + slot extraction.
    if llm_enabled():
        try:
            rr = interpret_with_openai(state)

            if rr.confidence >= llm_min_confidence() and rr.intent != Intent.UNKNOWN:
                # Update language only when the user explicitly requests a switch.
                if rr.language and explicit_language_switch(state.user_message):
                    state.preferred_language = rr.language

                # End-of-conversation is handled here (not as a separate node).
                if rr.intent == Intent.END:
                    state.mode = Mode.END
                    state.should_end = True
                    state.assistant_message = t(state, "ended")
                    state.next_node = "echo"
                    return state

                # Recommendation slots
                if rr.family is not None:
                    state.recommended_family = rr.family
                if rr.audience is not None:
                    state.recommended_audience = rr.audience
                if rr.max_price is not None:
                    state.recommended_max_price = rr.max_price
                if rr.min_price is not None:
                    state.recommended_min_price = rr.min_price

                # Apply product_id only if it appears in the raw user text.
                if rr.product_id is not None and re.search(rf"\b{rr.product_id}\b", state.user_message or ""):
                    state.selected_product_id = rr.product_id

                if _can_accept_intent(state, rr.intent):
                    state.last_intent = rr.intent.value
                    state.last_confidence = rr.confidence
                    state.next_node = _INTENT_TO_NODE.get(rr.intent, "echo")
                    return state

        except Exception:
            # Intentionally silent: deterministic rules already cover core behavior.
            # In production, this would be logged/observed; for the coding challenge we keep output clean.
            pass

    # 3) Fallback
    state.next_node = "echo"
    return state
