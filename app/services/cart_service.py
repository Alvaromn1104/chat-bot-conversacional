from __future__ import annotations

from app.engine.state import ConversationState

from .catalog_service import get_catalog


def calculate_cart_total(state: ConversationState) -> float:
    catalog = get_catalog()
    total = 0.0
    for pid in state.cart:
        p = next((x for x in catalog if x.id == pid), None)
        if not p:
            continue
        total += p.price
    return total
