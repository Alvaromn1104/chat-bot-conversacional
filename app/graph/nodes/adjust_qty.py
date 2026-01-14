from __future__ import annotations

import re

from app.engine.state import ConversationState, Mode
from app.tools import (
    tool_get_product,
    tool_set_cart_qty,
    tool_cart_total,
    tool_find_products_by_name,
)
from app.utils import parse_adjustment
from app.ux import t


def _norm(text: str | None) -> str:
    return (text or "").strip().casefold()


def _parse_choice_to_product_id(text: str, candidates: list[int]) -> int | None:
    """
    Accepts:
    - product id: "319"
    - option number: "1" / "2"
    """
    tt = _norm(text)

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


def _ask_pick_one(state: ConversationState, header_key: str, candidates: list[int]) -> None:
    lines = [t(state, header_key)]
    for i, pid in enumerate(candidates, start=1):
        p = tool_get_product(pid)
        if p:
            lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")
    lines.append(t(state, "pick_number_id_or_name"))
    state.assistant_message = "\n".join(lines)



def adjust_cart_qty_node(state: ConversationState) -> ConversationState:
    lang = state.preferred_language or "en"

    # --------------------------------------------------
    # 0) Resolving a pending clarification → consume user choice
    # --------------------------------------------------
    if state.pending_product_op == "set_qty" and state.candidate_products:
        target_qty = state.pending_qty
        if target_qty is None:
            state.assistant_message = t(state, "fallback_ok")
            return state

        chosen = _parse_choice_to_product_id(state.user_message, state.candidate_products)
        if chosen is None:
            state.assistant_message = t(state, "pick_number_id_or_name")
            return state

        product_id = chosen

        # ✅ clear clarification state now (break loops)
        state.candidate_products = []
        state.pending_product_op = None
        state.pending_qty = None

        product = tool_get_product(product_id)
        if not product:
            state.assistant_message = t(state, "product_not_found", product_id=product_id)
            return state

        ok, new_qty = tool_set_cart_qty(state, product_id, target_qty)
        if not ok:
            state.assistant_message = t(state, "qty_update_failed")
            return state

        total = tool_cart_total(state)

        state.mode = Mode.CART
        state.ui_product = product
        state.ui_products = []
        state.ui_cart_total = total

        state.last_cart_product_ids = [product_id]
        state.last_cart_op = "set_qty"
        state.last_cart_qty = new_qty

        state.assistant_message = t(
            state,
            "qty_set_ok",
            product_id=product.id,
            brand=product.brand or "",
            name=product.name,
            qty=new_qty,
            total=total,
        )
        return state

    # --------------------------------------------------
    # 1) Normal parse ("mejor que sea 1 ...")
    # --------------------------------------------------
    target_qty, hint = parse_adjustment(state.user_message)
    if target_qty is None:
        state.assistant_message = t(state, "fallback_ok")
        return state

    product_id: int | None = None

    if hint:
        matches = tool_find_products_by_name(hint)

        if len(matches) == 1:
            product_id = matches[0]

        elif len(matches) > 1:
            state.candidate_products = matches
            state.pending_product_op = "set_qty"
            state.pending_qty = target_qty

            _ask_pick_one(state, "adjust_multiple_found", matches)
            return state

        else:
            # ✅ if hint is garbage (e.g. "sean"), fall back to last_cart_product_ids
            hint = None

    if product_id is None:
        if len(state.last_cart_product_ids) == 1:
            product_id = state.last_cart_product_ids[0]

        elif len(state.last_cart_product_ids) > 1:
            state.candidate_products = state.last_cart_product_ids
            state.pending_product_op = "set_qty"
            state.pending_qty = target_qty

            _ask_pick_one(state, "adjust_which_of_these", state.last_cart_product_ids)
            return state

        else:
            state.assistant_message = t(state, "need_product_id_or_name")
            return state

    product = tool_get_product(product_id)
    if not product:
        state.assistant_message = t(state, "product_not_found", product_id=product_id)
        return state

    ok, new_qty = tool_set_cart_qty(state, product_id, target_qty)
    if not ok:
        state.assistant_message = t(state, "qty_update_failed")
        return state

    total = tool_cart_total(state)

    state.mode = Mode.CART
    state.ui_product = product
    state.ui_products = []
    state.ui_cart_total = total

    state.last_cart_product_ids = [product_id]
    state.last_cart_op = "set_qty"
    state.last_cart_qty = new_qty

    state.assistant_message = t(
        state,
        "qty_set_ok",
        product_id=product.id,
        brand=product.brand or "",
        name=product.name,
        qty=new_qty,
        total=total,
    )
    return state
