from __future__ import annotations

from app.engine.state import ConversationState
from .common_rules import msg_l


def rule_show_catalog(state: ConversationState) -> bool:
    """
    Route to catalog view when the user asks to browse available products.

    This rule uses a deterministic keyword match (ES/EN) to keep routing fast,
    predictable, and independent from the LLM.
    """
    text = msg_l(state)

    if any(
        k in text
        for k in [
            # ES
            "catálogo", "catalogo", "ver el catálogo", "ver el catalogo", "el catálogo", "el catalogo",
            "que perfumes tienes", "que tienes para mostrarme", "que vendes", "que productos tienes",
            # EN
            "catalog", "catalogue", "the catalog", "show the catalog", "show me the catalog",
            "what perfumes do you have", "what do you have", "what do you sell",
            "list perfumes", "show me what you have",
        ]
    ):
        state.next_node = "show_catalog"
        return True

    return False
