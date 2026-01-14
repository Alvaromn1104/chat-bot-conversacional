from __future__ import annotations

import re

from app.engine.state import ConversationState


# Strong checkout intent detector (ES/EN).
# Centralized here to avoid duplicating checkout keywords across multiple rules.
CHECKOUT_RE = re.compile(
    r"\b("
    r"checkout|pay|payment|"
    r"pago|pagar|hacer el pago|"
    r"finalizar(?:\s+la)?\s+compra|tramitar(?:\s+pedido)?"
    r")\b",
    re.IGNORECASE,
)


def msg_l(state: ConversationState) -> str:
    """Lowercased and trimmed user message convenience helper."""
    return (state.user_message or "").strip().lower()


def explicit_language_switch(text: str) -> bool:
    """
    Detect explicit user requests to switch language.

    This is handled deterministically to avoid any ambiguity before routing
    the turn through the graph/LLM.
    """
    tt = (text or "").lower()
    return any(
        k in tt
        for k in [
            "en español",
            "en espanol",
            "habla español",
            "habla espanol",
            "in english",
            "speak english",
            "english please",
        ]
    )


def detect_language_heuristic(text: str) -> str | None:
    """
    Best-effort language detection heuristic (ES/EN).

    Used when the user did not explicitly request a language switch. This keeps
    routing fast and avoids spending an LLM call on language detection alone.
    """
    tt = (text or "").lower()

    if any(k in tt for k in ["en español", "en espanol", "habla español", "habla espanol"]):
        return "es"
    if any(k in tt for k in ["in english", "speak english", "english please"]):
        return "en"

    if any(
        k in tt
        for k in [
            "show", "tell me", "details", "add", "remove", "delete", "cart",
            "pay", "recommend", "under", "cheaper", "please", "in english",
            "make it", "set it", "change it", "only", "just", "instead",
            "yes", "help",
        ]
    ):
        return "en"

    # Common Spanish punctuation/diacritics.
    if any(ch in tt for ch in ["¿", "¡", "ñ", "á", "é", "í", "ó", "ú"]):
        return "es"

    if any(
        k in tt
        for k in [
            "añade","anade","añadir","quita","quitar","carrito",
            "muestrame","muéstrame","ensename","enseñame","enséñame",
            "recomendar","recomendarme","recomiendame","recomiéndame",
            "precio","catalogo","catálogo","menos de","euros","hombre","mujer",
            "quiero","puedes","me puedes","amaderado","amaderados","maderoso","maderosos",
            "cítrico","citrico","cítricos","citricos","floral","florales",
            "oriental","orientales","ámbar","ambar","acuático","acuatico","acuáticos","acuaticos",
            "marino","marinos","aromático","aromatico","aromáticos","aromaticos",
            "dulce","dulces","gourmand","afrutado","afrutados","frutal","frutales",
            "cuero","mejor","solo","que sea","que sean","cámbialo","cambialo","en vez de",
        ]
    ):
        return "es"

    return None
