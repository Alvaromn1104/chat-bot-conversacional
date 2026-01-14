from __future__ import annotations

from typing import Dict, List
import re

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
    Accepts:
    - product id: "315"
    - option number: "1" / "2"
    """
    tt = (text or "").strip().lower()

    m_id = re.search(r"\b(\d{3})\b", tt)
    if m_id:
        pid = int(m_id.group(1))
        return pid if pid in candidates else None

    m_opt = re.search(r"\b(\d+)\b", tt)
    if m_opt:
        idx = int(m_opt.group(1)) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]

    return None


def bulk_cart_update_node(state: ConversationState) -> ConversationState:
    actions: List[CartAction] = state.pending_actions or []

    # --------------------------------------------------
    # 0) Resolving a previous bulk clarification
    # --------------------------------------------------
    pending_bulk_op = state.pending_bulk_op
    pending_bulk_qty = state.pending_bulk_qty

    if pending_bulk_op and state.candidate_products:
        product_id = _parse_choice_to_product_id(state.user_message, state.candidate_products)
        if product_id is None:
            state.assistant_message = t(state, "bulk_reply_number_id")
            return state

        op = CartOp(pending_bulk_op)
        qty = int(pending_bulk_qty or 1)
        actions.append(CartAction(op=op, product_id=product_id, qty=qty))

        # clear bulk clarification state
        state.candidate_products = []
        state.pending_bulk_op = None
        state.pending_bulk_qty = None

    # --------------------------------------------------
    # 1) Resolve pending_name_actions (created by parser)
    # --------------------------------------------------
    # ✅ resolve pending_name_actions as a QUEUE (do not lose remaining actions)
    pending_name_actions = getattr(state, "pending_name_actions", None) or []
    while pending_name_actions:
        packed = pending_name_actions.pop(0)  # consume 1

        # persist the remainder in state in case we need to return early
        state.pending_name_actions = pending_name_actions

        try:
            op_s, qty_s, hint = packed.split("|", 2)
            op = CartOp(op_s)
            qty = int(qty_s)
        except Exception:
            continue

        matches = tool_find_products_by_name(hint)

        if len(matches) == 1:
            actions.append(CartAction(op=op, product_id=matches[0], qty=qty))
            continue

        if len(matches) > 1:
            # Ask clarification, ✅ KEEP actions resolved so far AND keep remaining name actions
            state.candidate_products = matches
            state.pending_bulk_op = op.value
            state.pending_bulk_qty = qty

            lines = [t(state, "multiple_matches_which_add")]
            for i, pid in enumerate(matches, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")
            lines.append(t(state, "reply_number_id"))

            state.pending_actions = actions  # keep resolved actions so far
            state.assistant_message = "\n".join(lines)
            return state

        # no match -> stop and inform (optional: you could continue instead)
        state.assistant_message = t(state, "bulk_none")
        return state

    # --------------------------------------------------
    # 2) Apply actions
    # --------------------------------------------------
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

    if affected:
        state.last_cart_product_ids = list(dict.fromkeys(affected))
        state.selected_product_id = state.last_cart_product_ids[-1]


    return state
