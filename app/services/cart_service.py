from __future__ import annotations

from app.engine.state import ConversationState
from app.services.catalog_service import get_product_by_id


def calculate_cart_total(state: ConversationState) -> float:
    """
    Calculate the total price of the current cart.

    The total is computed dynamically from product prices in the catalog
    to avoid trusting potentially stale client-side data.
    """
    total = 0.0
    for item in state.cart:
        p = get_product_by_id(item.product_id)
        if not p:
            # Skip missing products defensively to avoid breaking the flow
            # if the catalog changes or data becomes inconsistent.
            continue
        total += p.price * item.qty
    return total
