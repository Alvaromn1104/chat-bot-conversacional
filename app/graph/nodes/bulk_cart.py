from __future__ import annotations

import re
from typing import Dict, List

from app.engine.state import ConversationState, Mode
from app.llm.router_schema import CartAction, CartOp
from app.tools import (
    tool_get_product,
    tool_add_to_cart,
    tool_remove_from_cart,
    tool_cart_total,
    tool_find_products_by_name,
)
from app.ux import t


def _parse_choice_to_product_id(text: str, candidates: list[int]) -> int | None:
    """
    Parse a user's clarification reply into a concrete product_id.

    Accepted inputs:
    - A 3-digit product ID (e.g., "315")
    - An option number (e.g., "1", "2") referring to the candidate list order

    Returns:
    - product_id if valid and present in candidates, otherwise None.
    """
    tt = (text or "").strip().lower()

    # Direct product ID
    m_id = re.fullmatch(r"(\d{3})", tt)
    if m_id:
        pid = int(m_id.group(1))
        return pid if pid in candidates else None

    # Option number
    m_opt = re.fullmatch(r"(\d+)", tt)
    if m_opt:
        idx = int(m_opt.group(1)) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]

    return None


def bulk_cart_update_node(state: ConversationState) -> ConversationState:
    """
    Apply multiple cart operations in a single turn.

    This node supports:
    - Bulk actions already parsed into `state.pending_actions`
    - Name-based actions queued in `state.pending_name_actions` (resolved via search + clarification)
    - Clarification loops using `state.candidate_products` and `state.pending_bulk_*`

    State-safety rule:
    - This node may preserve pending actions across turns ONLY when it must ask for clarification.
    - Once the batch is applied (or aborted), it clears all relevant `pending_*` fields to avoid leaks.
    """
    # NOTE: We intentionally append to the existing list when resuming a batch after clarification.
    # This preserves actions resolved in previous steps of the same bulk flow.
    actions: List[CartAction] = state.pending_actions or []

    # --------------------------------------------------
    # 0) Resolve a previous clarification
    # --------------------------------------------------
    # If the node previously asked "Which one did you mean?", the user's next message should
    # pick one of `state.candidate_products`. We then reconstruct the pending CartAction.
    pending_bulk_op = state.pending_bulk_op
    pending_bulk_qty = state.pending_bulk_qty

    if pending_bulk_op and state.candidate_products:
        product_id = _parse_choice_to_product_id(state.user_message, state.candidate_products)
        if product_id is None:
            # Keep clarification state intact; user needs to reply with a valid option/ID.
            state.assistant_message = t(state, "bulk_reply_number_id")
            return state

        op = CartOp(pending_bulk_op)
        qty = int(pending_bulk_qty or 1)
        actions.append(CartAction(op=op, product_id=product_id, qty=qty))

        # Clear only the clarification flags; we still need to apply the batch.
        state.candidate_products = []
        state.pending_bulk_op = None
        state.pending_bulk_qty = None

    # --------------------------------------------------
    # 1) Resolve queued name-based actions
    # --------------------------------------------------
    # `pending_name_actions` is processed like a queue. If we hit ambiguity, we return early
    # but keep:
    # - actions resolved so far
    # - remaining name actions to retry next turn
    pending_name_actions = getattr(state, "pending_name_actions", None) or []
    while pending_name_actions:
        packed = pending_name_actions.pop(0)

        # Persist remaining items before any possible early return (clarification).
        state.pending_name_actions = pending_name_actions

        try:
            op_s, qty_s, hint = packed.split("|", 2)
            op = CartOp(op_s)
            qty = int(qty_s)
        except Exception:
            # Malformed entry: ignore and continue so one bad item doesn't break the batch.
            continue

        matches = tool_find_products_by_name(hint)

        if len(matches) == 1:
            actions.append(CartAction(op=op, product_id=matches[0], qty=qty))
            continue

        if len(matches) > 1:
            # Ambiguous match: ask user which product they meant.
            # We must preserve state to resume the same bulk batch next turn.
            state.candidate_products = matches
            state.pending_bulk_op = op.value
            state.pending_bulk_qty = qty

            lines = [t(state, "multiple_matches_which_add")]
            for i, pid in enumerate(matches, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")
            lines.append(t(state, "reply_number_id"))

            state.pending_actions = actions
            state.assistant_message = "\n".join(lines)
            return state

        # No match: abort this bulk batch (user-friendly + prevents stale pending state).
        state.assistant_message = t(state, "bulk_none")
        state.pending_actions = []
        state.pending_name_actions = []
        state.pending_bulk_op = None
        state.pending_bulk_qty = None
        state.candidate_products = []
        return state

    # --------------------------------------------------
    # 2) Apply actions
    # --------------------------------------------------
    # Build a local view of cart quantities to validate removals consistently during the batch.
    in_cart: Dict[int, int] = {item.product_id: item.qty for item in state.cart}
    lines: List[str] = []
    affected: list[int] = []

    for a in actions:
        op = a.op
        product_id = a.product_id
        qty = a.qty

        product = tool_get_product(product_id)
        if not product:
            lines.append(t(state, "bulk_not_found", product_id=product_id))
            continue

        product_label = f"[{product.id}] {product.brand} - {product.name}"

        if op == CartOp.ADD:
            ok, added = tool_add_to_cart(state, product_id, qty=qty)
            if not ok or added <= 0:
                lines.append(t(state, "bulk_no_stock", product_label=product_label))
                continue

            note = ""
            if added < qty:
                note = t(state, "bulk_partial_add_note", qty=qty, added=added)

            lines.append(t(state, "bulk_added", added=added, product_label=product_label, note=note))
            in_cart[product_id] = in_cart.get(product_id, 0) + added
            affected.append(product_id)
            continue

        if op == CartOp.REMOVE:
            current_qty = in_cart.get(product_id, 0)
            if current_qty <= 0:
                lines.append(t(state, "bulk_not_in_cart", product_label=product_label))
                continue

            if qty > current_qty:
                lines.append(
                    t(
                        state,
                        "bulk_cannot_remove",
                        qty=qty,
                        product_label=product_label,
                        current_qty=current_qty,
                    )
                )
                continue

            ok, removed = tool_remove_from_cart(state, product_id, qty=qty)
            if not ok or removed <= 0:
                lines.append(t(state, "bulk_remove_failed", product_label=product_label))
                continue

            lines.append(t(state, "bulk_removed", removed=removed, product_label=product_label))

            remaining = current_qty - removed
            if remaining <= 0:
                in_cart.pop(product_id, None)
            else:
                in_cart[product_id] = remaining

            affected.append(product_id)
            continue

        # Defensive fallback (should not occur due to schema validation).
        lines.append(t(state, "bulk_not_found", product_id=product_id))

    total = tool_cart_total(state)
    lines.append("")
    lines.append(t(state, "bulk_total", total=total))
    lines.append(t(state, "bulk_next"))

    state.mode = Mode.CART
    state.assistant_message = "\n".join(lines)

    state.ui_product = None
    state.ui_products = []
    state.ui_cart_total = total

    # Provide conversational context for follow-up commands like "add 1 more".
    if affected:
        state.last_cart_product_ids = list(dict.fromkeys(affected))
        state.selected_product_id = state.last_cart_product_ids[-1]

    # --------------------------------------------------
    # 3) Clear pending state after the batch completes
    # --------------------------------------------------
    # Without this, subsequent turns may reuse stale pending actions and produce incorrect routing.
    state.pending_actions = []
    state.pending_name_actions = []
    state.pending_bulk_op = None
    state.pending_bulk_qty = None
    state.candidate_products = []

    return state
