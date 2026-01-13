from __future__ import annotations

import os
import re
import logging  # ✅
from app.engine.state import ConversationState, Mode


logger = logging.getLogger("app.routing.selectors")

def wants_catalog(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "catalog", "catalogue", "perfume", "perfumes", "products", "list",
        "available", "what do you have", "what do you sell"
    ]
    return any(k in t for k in keywords)


def wants_product_detail(text: str) -> bool:
    t = (text or "").lower().strip()

    show_verbs = [
        # EN
        "show", "details", "tell me", "see",
        # ES
        "muestrame", "muéstrame", "enseñame", "enséñame", "ver", "detalles",
    ]

    if not any(v in t for v in show_verbs):
        return False

    if any(c.isdigit() for c in t):
        return True

    fillers = {"el", "la", "los", "las", "de", "del", "un", "una", "por", "favor"}
    tokens = [x for x in re.split(r"\s+", t) if x and x not in fillers]

    return len(tokens) >= 2


def wants_add_to_cart(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        # EN
        "add", "add to cart", "buy", "i want it", "i'll take it", "take it", "purchase",
        # ES
        "añade", "anade", "añadir", "agrega", "mete", "pon", "quiero", "comprar", "llevar",
    ]

    strong = [
        "add", "take", "buy", "purchase",
        "añade", "anade", "añadir", "agrega", "mete", "pon", "comprar", "llevar",
    ]

    return any(k in t for k in keywords) and any(s in t for s in strong)


def wants_remove_from_cart(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        # EN
        "remove", "delete", "take out", "drop",
        # ES
        "quita", "quitar", "saca", "sacar", "elimina", "eliminar", "borra", "borrar",
    ]
    return any(k in t for k in keywords)


def wants_view_cart(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in ["view cart", "show cart", "my cart", "cart contents"])


def wants_checkout(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in ["checkout", "pay", "purchase", "place order"])


def _llm_enabled() -> bool:
    return os.getenv("LLM_ROUTER_ENABLED", "true").lower() == "true"


def _min_confidence() -> float:
    try:
        return float(os.getenv("LLM_MIN_CONFIDENCE", "0.6"))
    except ValueError:
        return 0.6
    
def wants_exit(text: str) -> bool:
    t = (text or "").lower().strip()
    patterns = [
        r"\b(salir|finalizar|terminar|cerrar|fin)\b",
        r"\b(exit|end|quit|bye)\b",
        r"\b(adiós|adios)\b",
    ]
    return any(re.search(p, t) for p in patterns)


def route_node(state: ConversationState) -> ConversationState:
    return state


def select_next_node_heuristic(state: ConversationState) -> str:
    logger.info(
        "HEURISTIC: msg=%r mode=%s should_end=%s",
        state.user_message, state.mode, state.should_end
    )

    if state.mode == Mode.CHECKOUT_CONFIRM:
        logger.info("HEURISTIC -> handle_checkout_confirmation (mode guard)")
        return "handle_checkout_confirmation"

    if state.mode == Mode.COLLECT_SHIPPING:
        logger.info("HEURISTIC -> collect_shipping (mode guard)")
        return "collect_shipping"

    if wants_exit(state.user_message):
        logger.info("HEURISTIC -> wants_exit=True (setting END flags)")
        state.mode = Mode.END
        state.should_end = True
        state.assistant_message = (
            "Conversación finalizada. Gracias por visitarnos."
            if (state.preferred_language or "en") == "es"
            else "Conversation ended. Thank you for visiting."
        )
        logger.info("HEURISTIC -> returning echo (will run echo_node!)")
        return "echo"

    # ... resto igual ...

    logger.info("HEURISTIC -> fallback echo")
    return "echo"


def select_next_node(state: ConversationState) -> str:
    logger.info(
        "SELECT_NEXT_NODE: next_node=%r mode=%s should_end=%s",
        state.next_node, state.mode, state.should_end
    )

    if state.should_end or state.mode == Mode.END:
        logger.info("SELECT_NEXT_NODE -> echo (hard stop)")
        return "echo"

    out = state.next_node or "echo"
    logger.info("SELECT_NEXT_NODE -> %s", out)
    return out
