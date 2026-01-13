from __future__ import annotations

import re

from app.engine.state import ConversationState, Mode
from app.graph.routing.rules import RULES, _explicit_language_switch, apply_recommend_heuristic
from app.graph.routing.selectors import _llm_enabled, _min_confidence, select_next_node_heuristic
from app.llm.openai_router import interpret_with_openai
from app.llm.router_schema import Intent


def interpret_user_node(state: ConversationState) -> ConversationState:
    print("[INTERPRET] msg=", repr(state.user_message), "mode=", state.mode)
    print("[INTERPRET] LLM_ENABLED=", _llm_enabled())

    # Hard stop: si ya terminó, no limpies nada
    if state.should_end or state.mode == Mode.END:
        return state

    # Reset de salida del turno (evita repetir el último mensaje)
    state.assistant_message = ""
    state.ui_products = []
    state.ui_product = None
    state.ui_cart_total = None

    # Evita reusar el nodo del turno anterior
    state.next_node = None

    # 1) Deterministic rules pipeline (works both with/without LLM)
    for rule in RULES:
        if rule(state):
            return state

    # 2) LLM router (only when enabled)
    if _llm_enabled():
        try:
            rr = interpret_with_openai(state)

            if rr.confidence >= _min_confidence() and rr.intent != Intent.UNKNOWN:
                if rr.language and _explicit_language_switch(state.user_message):
                    state.preferred_language = rr.language

                if rr.intent == Intent.END:
                    state.mode = Mode.END
                    state.should_end = True
                    state.assistant_message = (
                        "Conversación finalizada. Gracias por visitarnos."
                        if (state.preferred_language or "en") == "es"
                        else "Conversation ended. Thank you for visiting."
                    )
                    return state

                if rr.family is not None:
                    state.recommended_family = rr.family
                if rr.audience is not None:
                    state.recommended_audience = rr.audience
                if rr.max_price is not None:
                    state.recommended_max_price = rr.max_price
                if rr.min_price is not None:
                    state.recommended_min_price = rr.min_price

                if rr.product_id is not None and re.search(rf"\b{rr.product_id}\b", state.user_message or ""):
                    state.selected_product_id = rr.product_id

                state.last_intent = rr.intent.value
                state.last_confidence = rr.confidence
                state.next_node = rr.intent.value
                return state

        except Exception:
            pass

        # ✅ fallback recomendación heurística si el LLM no resolvió
        if apply_recommend_heuristic(state):
            return state

    # 3) Fallback heuristic
    state.next_node = select_next_node_heuristic(state)
    return state
