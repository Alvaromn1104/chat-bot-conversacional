from __future__ import annotations

import re

from app.engine.state import ConversationState


def rule_pending_product(state: ConversationState) -> bool:
    """
    Resume a pending product-related operation that requires user clarification.

    If `pending_product_op` is set and candidate products exist, route to the
    appropriate disambiguation/continuation node. A standalone number in the user
    message is treated as a selection signal (e.g., index or product id).
    """
    if state.pending_product_op and state.candidate_products:
        if re.search(r"\b(\d{1,3})\b", state.user_message or ""):
            state.next_node = (
                "adjust_cart_qty"
                if state.pending_product_op == "set_qty"
                else "resolve_product_choice"
            )
            return True

        # If no explicit selection is detected, prompt/resolve product choice.
        state.next_node = "resolve_product_choice"
        return True

    return False


def rule_product_detail_by_id(state: ConversationState) -> bool:
    """
    Route to product detail when the user requests details and includes a product id.

    Heuristic: product IDs are expected to be 3 digits (catalog convention).
    """
    msg_l = (state.user_message or "").strip().lower()
    if re.search(r"\b\d{3}\b", state.user_message or "") and any(
        k in msg_l for k in ["muestrame", "muéstrame", "enseñame", "enséñame", "show me"]
    ):
        state.next_node = "show_product_detail"
        return True
    return False


def rule_product_detail_by_name(state: ConversationState) -> bool:
    """
    Route to product detail when the user requests "show me" without an explicit id.

    This allows name-based matching/lookup inside the product detail node.
    """
    msg_l = (state.user_message or "").strip().lower()
    if any(k in msg_l for k in ["muestrame", "muéstrame", "enseñame", "enséñame", "show me"]):
        if not re.search(r"\b\d{3}\b", state.user_message or ""):
            state.next_node = "show_product_detail"
            return True
    return False
