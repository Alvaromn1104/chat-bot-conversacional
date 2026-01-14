from __future__ import annotations

from app.engine.state import ConversationState, Mode
from app.tools import (
    tool_list_catalog,
    tool_get_product,
    tool_add_to_cart,
    tool_remove_from_cart,
    tool_cart_total,
    tool_find_products_by_name,
)
from app.utils import parse_qty_and_product_id, parse_qty_only
from app.ux import t


def add_to_cart_node(state: ConversationState) -> ConversationState:
    """
    Add a product to the cart.

    Resolution strategy:
    - Prefer explicit 3-digit product IDs.
    - If no ID, try name-based search from the user message.
    - Fall back to conversational context (`selected_product_id`) only if name search fails.
    """
    qty, parsed_product_id = parse_qty_and_product_id(state.user_message)

    if qty is None:
        q2 = parse_qty_only(state.user_message)
        if q2 is not None:
            qty = q2
    qty = qty or 1

    product_id = parsed_product_id

    if not product_id:
        matches = tool_find_products_by_name(state.user_message)

        if len(matches) == 1:
            product_id = matches[0]
            state.selected_product_id = product_id

        elif len(matches) > 1:
            state.candidate_products = matches
            state.pending_product_op = "add"
            state.pending_qty = qty

            lines = [t(state, "multiple_matches_which_add")]
            for i, pid in enumerate(matches, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")
            lines.append(t(state, "reply_number_id_name"))

            state.assistant_message = "\n".join(lines)
            return state

        else:
            
            product_id = state.selected_product_id

    if not product_id:
        state.assistant_message = t(state, "need_product_id_add")
        return state

    product = tool_get_product(product_id)
    if not product:
        state.assistant_message = t(state, "product_not_found", product_id=product_id)
        return state

    ok, added = tool_add_to_cart(state, product_id, qty=qty)
    product_label = f"[{product.id}] {product.brand} - {product.name}"

    if not ok or added <= 0:
        state.assistant_message = t(state, "add_no_stock", product_label=product_label)
        return state

    note = ""
    if added < qty:
        note = t(state, "cart_partial_add_note", qty=qty, added=added)

    state.mode = Mode.CART
    state.assistant_message = (
        t(state, "add_ok", added=added, product_label=product_label, note=note)
        + "\n"
        + t(state, "cart_next_after_add")
    )

    state.ui_product = product
    state.ui_products = []
    state.ui_cart_total = tool_cart_total(state)

    state.last_cart_product_ids = [product_id]
    state.last_cart_op = "add"
    state.last_cart_qty = added

    return state


def view_cart_node(state: ConversationState) -> ConversationState:
    """Render the cart contents and total."""
    if not state.cart:
        state.assistant_message = t(state, "cart_empty")
        return state

    catalog = tool_list_catalog()
    lines = [t(state, "cart_header")]

    for item in state.cart:
        p = next((x for x in catalog if x.id == item.product_id), None)
        if not p:
            continue
        subtotal = p.price * item.qty
        lines.append(
            f"- [{p.id}] {p.brand} - {p.name} — €{p.price:.2f} x {item.qty} = €{subtotal:.2f}"
        )

    total = tool_cart_total(state)

    lines.append("")
    lines.append(t(state, "cart_total", total=total))
    lines.append(t(state, "cart_next_after_action"))

    state.assistant_message = "\n".join(lines)
    state.mode = Mode.CART

    state.ui_product = None
    state.ui_products = []
    state.ui_cart_total = total

    return state


def remove_from_cart_node(state: ConversationState) -> ConversationState:
    """
    Remove a product from the cart.

    Resolution strategy mirrors `add_to_cart_node`:
    - Prefer explicit 3-digit product IDs.
    - Fall back to conversational context (`selected_product_id`).
    - If still ambiguous, try name-based search and request clarification when needed.
    """
    qty, parsed_product_id = parse_qty_and_product_id(state.user_message)
    product_id = parsed_product_id or state.selected_product_id

    # If no product ID was found, attempt to extract a standalone quantity.
    if not product_id and qty is None:
        q2 = parse_qty_only(state.user_message)
        if q2 is not None:
            qty = q2

    qty = qty or 1

    if not product_id:
        matches = tool_find_products_by_name(state.user_message)

        if len(matches) == 1:
            product_id = matches[0]
        elif len(matches) > 1:
            state.candidate_products = matches
            state.pending_product_op = "remove"
            state.pending_qty = qty

            lines = [t(state, "multiple_matches_which_remove")]
            for i, pid in enumerate(matches, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")
            lines.append(t(state, "reply_number_id"))

            state.assistant_message = "\n".join(lines)
            return state
        else:
            state.assistant_message = t(state, "need_product_id_remove")
            return state

    ok, removed = tool_remove_from_cart(state, product_id, qty=qty)
    if not ok or removed <= 0:
        state.assistant_message = t(state, "remove_not_in_cart", product_id=product_id)
        return state

    note = ""
    if removed < qty:
        note = t(state, "cart_partial_remove_note", qty=qty, removed=removed)

    state.mode = Mode.CART
    product = tool_get_product(product_id)
    product_label = f"[{product.id}] {product.brand} - {product.name}" if product else str(product_id)

    state.assistant_message = (
        t(state, "remove_ok", removed=removed, product_label=product_label, note=note)
        + "\n"
        + t(state, "cart_next_after_action")
    )

    state.ui_product = product if product else None
    state.ui_products = []
    state.ui_cart_total = tool_cart_total(state)

    state.last_cart_product_ids = [product_id]
    state.last_cart_op = "remove"
    state.last_cart_qty = removed

    return state
