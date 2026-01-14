from __future__ import annotations

import re

from app.engine.state import ConversationState
from .common_rules import msg_l

_ADD_VERBS = {
    "añade", "anade", "añadir", "añademe", "añádeme", "anademe",
    "agrega", "agrégame", "agregame", "mete", "pon", "add", "put", "take", "buy",
}

_REMOVE_VERBS = {
    "quita", "quítame", "quitame", "quitar",
    "remove", "delete", "drop", "saca", "borra", "elimina",
}

_ID_3DIGIT_RE = re.compile(r"\b\d{3}\b")


def rule_cart_op_by_name_fallback(state: ConversationState) -> bool:
    """
    Route add/remove intents without a 3-digit product ID to the cart nodes.

    This enables name-based resolution inside the corresponding node (via tools.search_tools).
    """
    text = msg_l(state)
    if not text:
        return False

    # If there is a 3-digit ID, other rules/parsers should handle it.
    if _ID_3DIGIT_RE.search(text):
        return False

    if any(v in text for v in _ADD_VERBS):
        state.next_node = "add_to_cart"
        return True

    if any(v in text for v in _REMOVE_VERBS):
        state.next_node = "remove_from_cart"
        return True

    return False
