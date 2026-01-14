from __future__ import annotations

import re

from app.engine.state import ConversationState
from app.tools import tool_get_product
from app.ux import t
from app.utils import parse_cart_commands, parse_adjustment, parse_qty_only
from .common_rules import msg_l


# Verbs commonly used to express item removal from the cart (ES/EN).
_REMOVE_VERBS = [
    "quitame", "quítame", "quita",
    "remove", "delete", "saca", "borra", "elimina",
]


def rule_adjust_qty(state: ConversationState) -> bool:
    """
    Detect quantity adjustment intent (e.g., "ponlo en 3", "set to 2").
    Routes to the cart quantity adjustment node when a target quantity is found.
    """
    target_qty, _ = parse_adjustment(state.user_message)
    if target_qty is not None:
        state.next_node = "adjust_cart_qty"
        return True
    return False


def rule_single_cart_command(state: ConversationState) -> bool:
    """
    Handle a single explicit cart command (add/remove) when unambiguous.

    If a remove command is detected and the cart contains multiple products without
    an explicit product id reference, the flow is routed to a disambiguation step.
    """
    msg = state.user_message or ""
    text = msg_l(state)

    actions = parse_cart_commands(msg)

    if len(actions) == 1:
        a = actions[0]

        # If removing and multiple cart items exist, require explicit product identification.
        if a.op.value == "remove" and len(state.cart) > 1:
            cart_ids = [x.product_id for x in state.cart]

            # "Explicit" means the message contains one of the cart product ids as a whole word.
            mentions_any_cart_id = any(re.search(rf"\b{pid}\b", text) for pid in cart_ids)

            if not mentions_any_cart_id:
                state.candidate_products = list(dict.fromkeys(cart_ids))
                state.pending_product_op = "remove"
                state.pending_qty = a.qty or 1
                state.next_node = "resolve_product_choice"
                return True

        # Normal case: a single add/remove command with a clear target product.
        state.selected_product_id = a.product_id
        state.pending_qty = a.qty
        state.next_node = "add_to_cart" if a.op.value == "add" else "remove_from_cart"
        return True

    # If a product was previously selected and the user issues a remove-like command with a quantity.
    if state.selected_product_id is not None:
        m = re.search(r"\b(\d+)\b", text)
        if m and any(
            k in text
            for k in ["quitame", "quítame", "quita", "remove", "delete", "saca", "borra"]
        ):
            qty = int(m.group(1))

            if len(state.cart) == 1:
                state.pending_qty = qty
                state.selected_product_id = state.cart[0].product_id
                state.next_node = "remove_from_cart"
                return True

            candidates = list(dict.fromkeys([x.product_id for x in state.cart]))

            if len(candidates) == 1:
                state.pending_qty = qty
                state.selected_product_id = candidates[0]
                state.next_node = "remove_from_cart"
                return True

            state.candidate_products = candidates
            state.pending_product_op = "remove"
            state.pending_qty = qty
            state.next_node = "resolve_product_choice"
            return True

    return False


def rule_remove_qty_only_needs_disambiguation(state: ConversationState) -> bool:
    """
    Handle remove commands that provide only a quantity (no explicit product id),
    when multiple products exist in the cart.

    In this case, the assistant should ask which product to remove and store
    the disambiguation context in the state.
    """
    # If another rule already prepared a response, do not override it.
    if (state.assistant_message or "").strip():
        return False

    # If a product choice is already pending, let the dedicated rule handle it.
    if state.pending_product_op and state.candidate_products:
        return False

    text = msg_l(state)
    if not text:
        return False

    # Must resemble a remove intent.
    if not any(v in text for v in _REMOVE_VERBS):
        return False

    # Heuristic: accept 1-2 digit quantities but avoid 3-digit product IDs.
    has_qty = re.search(r"\b\d{1,2}\b", text) is not None
    has_product_id = re.search(r"\b\d{3}\b", text) is not None
    if not has_qty or has_product_id:
        return False

    cart_ids = list(dict.fromkeys([x.product_id for x in state.cart]))
    if len(cart_ids) <= 1:
        return False

    m = re.search(r"\b(\d{1,2})\b", text)
    qty = int(m.group(1)) if m else 1

    # Persist disambiguation context for the next user reply.
    state.candidate_products = cart_ids
    state.pending_product_op = "remove"
    state.pending_qty = qty

    # Build a numbered menu for the user (by index or product ID).
    lines = [t(state, "multiple_matches_which_remove")]
    for i, pid in enumerate(cart_ids, start=1):
        p = tool_get_product(pid)
        if p:
            lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")
    lines.append(t(state, "reply_number_id"))

    state.assistant_message = "\n".join(lines)

    # Do not execute any graph node this turn; wait for user clarification.
    state.next_node = None
    return True


def rule_implicit_cart_op(state: ConversationState) -> bool:
    """
    Handle implicit 'add' commands that rely on a previously selected product.

    Example: "añade 2" when the product context is already known.
    """
    text = msg_l(state)
    if not text:
        return False

    add_verbs = ["añade", "anade", "añadir", "agrega", "mete", "pon", "add", "put", "take"]
    if not any(v in text for v in add_verbs):
        return False

    qty = parse_qty_only(state.user_message) or 1

    product_id: int | None = None
    if state.selected_product_id:
        product_id = state.selected_product_id
    elif len(state.last_cart_product_ids) == 1:
        product_id = state.last_cart_product_ids[0]
        state.selected_product_id = product_id
    else:
        return False

    state.pending_qty = qty
    state.next_node = "add_to_cart"
    return True


def rule_view_cart(state: ConversationState) -> bool:
    """
    Route to the cart view when the user asks to see the current cart contents.
    """
    text = msg_l(state)
    if any(
        k in text
        for k in [
            "carrito", "ver carrito", "muéstrame el carrito", "muestrame el carrito",
            "cart", "show cart", "show me the cart", "view cart", "que llevo en el carrito",
        ]
    ):
        state.next_node = "view_cart"
        return True
    return False


def rule_cart_commands_any(state: ConversationState) -> bool:
    """
    Fallback handler for parsed cart commands.

    - If a single action exists, route directly to add/remove.
    - If multiple actions exist, store them and route to bulk update.
    """
    actions = parse_cart_commands(state.user_message)

    if not actions:
        return False

    if len(actions) == 1:
        a = actions[0]
        state.selected_product_id = a.product_id
        state.pending_qty = a.qty
        state.next_node = "add_to_cart" if a.op.value == "add" else "remove_from_cart"
        return True

    state.pending_actions = actions
    state.next_node = "bulk_cart_update"
    return True
