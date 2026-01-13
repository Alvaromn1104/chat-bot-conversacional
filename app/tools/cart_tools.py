from __future__ import annotations

from app.engine.state import ConversationState, CartItem
from app.tools.catalog_tools import tool_get_product

def tool_cart_total(state: ConversationState) -> float:
    total = 0.0
    for item in state.cart:
        p = tool_get_product(item.product_id)
        if p:
            total += p.price * item.qty
    return total

def tool_set_cart_qty(state: ConversationState, product_id: int, qty: int) -> tuple[bool, int]:
    """
    Set the cart quantity for a product to an absolute value.

    Rules:
    - qty <= 0 => remove item from cart (treat as delete)
    - qty > stock => clamp to max available stock
    - if product not found => fail
    - if product not in cart and qty > 0 => add it
    """
    product = tool_get_product(product_id)
    if not product:
        return False, 0

    if qty <= 0:
        # remove entirely if exists
        for i, item in enumerate(state.cart):
            if item.product_id == product_id:
                state.cart.pop(i)
                return True, 0
        return True, 0

    # clamp to stock
    new_qty = min(qty, product.stock)

    existing = next((x for x in state.cart if x.product_id == product_id), None)
    if existing:
        existing.qty = new_qty
    else:
        state.cart.append(CartItem(product_id=product_id, qty=new_qty))

    return True, new_qty


def tool_add_to_cart(state: ConversationState, product_id: int, qty: int = 1) -> tuple[bool, int]:
    if qty < 1:
        return False, 0

    product = tool_get_product(product_id)
    if not product:
        return False, 0

    existing = next((x for x in state.cart if x.product_id == product_id), None)
    current = existing.qty if existing else 0

    can_add = max(0, product.stock - current)
    added = min(qty, can_add)

    if added <= 0:
        return False, 0

    if existing:
        existing.qty += added
    else:
        state.cart.append(CartItem(product_id=product_id, qty=added))

    return True, added


def tool_remove_from_cart(state: ConversationState, product_id: int, qty: int = 1) -> tuple[bool, int]:
    if qty < 1:
        return False, 0

    for i, item in enumerate(state.cart):
        if item.product_id == product_id:
            removed = min(qty, item.qty)
            item.qty -= removed
            if item.qty == 0:
                state.cart.pop(i)
            return True, removed

    return False, 0

