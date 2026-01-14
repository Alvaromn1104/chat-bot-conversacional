from __future__ import annotations

import re

from app.engine.state import ConversationState
from app.utils import parse_cart_commands_by_name


def rule_pending_bulk(state: ConversationState) -> bool:
    """
    Continue a pending bulk cart operation if the user provides a quantity.

    This rule is triggered when a previous step detected multiple target products
    and stored them in `candidate_products` alongside a pending bulk operation.
    """
    # Defensive access to support state evolution (avoids AttributeError if field is missing).
    if getattr(state, "pending_bulk_op", None) and state.candidate_products:
        # Detect a standalone numeric quantity (1-3 digits) in the user message.
        if re.search(r"\b(\d{1,3})\b", state.user_message or ""):
            state.next_node = "bulk_cart_update"
            return True

        # If the user didn't provide a valid quantity, clear pending bulk state to avoid stale flows.
        state.pending_bulk_op = None
        state.pending_bulk_qty = None
        state.candidate_products = []
    return False


def rule_bulk_cart_names(state: ConversationState) -> bool:
    """
    Detect multiple cart actions expressed by product name in a single user message.

    If at least two actions are present and at least one requires name resolution,
    queue actions and route to the bulk cart update node.
    """
    actions_with_ids, name_actions = parse_cart_commands_by_name(state.user_message)

    # The router only treats this as a bulk operation when multiple actions exist.
    if (len(actions_with_ids) + len(name_actions) >= 2) and name_actions:
        state.pending_actions = actions_with_ids

        # Serialize name-based actions for later resolution.
        # Format: "op|qty|hint" (kept simple to pass through the state safely).
        state.pending_name_actions = [
            f"{op.value}|{qty}|{hint}" for op, qty, hint in name_actions
        ]

        state.next_node = "bulk_cart_update"
        return True

    return False
