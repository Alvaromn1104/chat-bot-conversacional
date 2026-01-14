from __future__ import annotations

from app.engine.state import ConversationState, CartItem
from app.tools.catalog_tools import tool_get_product
from app.services.cart_service import calculate_cart_total


def tool_cart_total(state: ConversationState) -> float:
    """
    Compute the current cart total.

    Delegates the calculation to the cart service to keep pricing logic centralized.
    """
    return calculate_cart_total(state)


def tool_set_cart_qty(
    state: ConversationState,
    product_id: int,
    qty: int,
) -> tuple[bool, int]:
    """
    Set the cart quantity for a product to an absolute value.

    Rules:
    - qty <= 0: remove the item from the cart
    - qty > available stock: clamp to maximum stock
    - product not found: operation fails
    - product not in cart and qty > 0: item is added
    """
    product = tool_get_product(product_id)
    if not product:
        return False, 0

    if qty <= 0:
        # Remove item entirely if present.
        for i, item in enumerate(state.cart):
            if item.product_id == product_id:
                state.cart.pop(i)
                return True, 0
        return True, 0

    # Clamp requested quantity to available stock.
    new_qty = min(qty, product.stock)

    existing = next((x for x in state.cart if x.product_id == product_id), None)
    if existing:
        existing.qty = new_qty
    else:
        state.cart.append(CartItem(product_id=product_id, qty=new_qty))

    return True, new_qty


def tool_add_to_cart(
    state: ConversationState,
    product_id: int,
    qty: int = 1,
) -> tuple[bool, int]:
    """
    Add a quantity of a product to the cart.

    The quantity added is limited by available stock.
    """
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


def tool_remove_from_cart(
    state: ConversationState,
    product_id: int,
    qty: int = 1,
) -> tuple[bool, int]:
    """
    Remove a quantity of a product from the cart.

    If the resulting quantity reaches zero, the item is removed entirely.
    """
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
