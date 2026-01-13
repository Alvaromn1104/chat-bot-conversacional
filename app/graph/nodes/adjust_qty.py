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


def _parse_choice_to_product_id(text: str, candidates: list[int]) -> int | None:
    """
    Accepts:
    - product id: "319"
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


def adjust_cart_qty_node(state: ConversationState) -> ConversationState:
    lang = state.preferred_language or "en"

    # --------------------------------------------------
    # 0) Resolving a pending clarification → consume user choice
    # --------------------------------------------------
    if state.pending_product_op == "set_qty" and state.candidate_products:
        target_qty = state.pending_qty
        if target_qty is None:
            state.assistant_message = "Vale." if lang == "es" else "Okay."
            return state

        chosen = _parse_choice_to_product_id(state.user_message, state.candidate_products)
        if chosen is None:
            state.assistant_message = (
                "Responde con el número, el ID o el nombre."
                if lang == "es"
                else "Reply with the number, the ID, or the name."
            )
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
            state.assistant_message = (
                "No he podido actualizar la cantidad."
                if lang == "es"
                else "I couldn't update the quantity."
            )
            return state

        total = tool_cart_total(state)

        state.mode = Mode.CART
        state.ui_product = product
        state.ui_products = []
        state.ui_cart_total = total

        state.last_cart_product_ids = [product_id]
        state.last_cart_op = "set_qty"
        state.last_cart_qty = new_qty

        state.assistant_message = (
            f"Perfecto ✅ Dejé [{product.id}] {product.brand} - {product.name} en {new_qty} unidad(es).\n\nTotal: €{total:.2f}"
            if lang == "es"
            else f"Done ✅ Set [{product.id}] {product.brand} - {product.name} to {new_qty} unit(s).\n\nTotal: €{total:.2f}"
        )
        return state

    # --------------------------------------------------
    # 1) Normal parse ("mejor que sea 1 ...")
    # --------------------------------------------------
    target_qty, hint = parse_adjustment(state.user_message)
    if target_qty is None:
        state.assistant_message = "Vale." if lang == "es" else "Okay."
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

            lines = [
                "He encontrado varias opciones. ¿Cuál quieres ajustar?"
                if lang == "es"
                else "I found multiple matches. Which one do you want to adjust?"
            ]

            for i, pid in enumerate(matches, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")

            lines.append(
                "Responde con el número, el ID o el nombre."
                if lang == "es"
                else "Reply with the number, the ID, or the name."
            )

            state.assistant_message = "\n".join(lines)
            return state

        else:
            # ✅ FIX: if hint is garbage (e.g. "sean"), fall back to last_cart_product_ids
            hint = None
                

    if product_id is None:
        if len(state.last_cart_product_ids) == 1:
            product_id = state.last_cart_product_ids[0]

        elif len(state.last_cart_product_ids) > 1:
            state.candidate_products = state.last_cart_product_ids
            state.pending_product_op = "set_qty"
            state.pending_qty = target_qty

            lines = [
                "¿A cuál de estos productos te refieres?"
                if lang == "es"
                else "Which of these products do you mean?"
            ]

            for i, pid in enumerate(state.last_cart_product_ids, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")

            lines.append(
                "Responde con el número, el ID o el nombre."
                if lang == "es"
                else "Reply with the number, the ID, or the name."
            )

            state.assistant_message = "\n".join(lines)
            return state

        else:
            state.assistant_message = (
                "¿De qué producto hablamos? Dime el ID o el nombre."
                if lang == "es"
                else "Which product do you mean? Tell me the ID or the name."
            )
            return state

    product = tool_get_product(product_id)
    if not product:
        state.assistant_message = t(state, "product_not_found", product_id=product_id)
        return state

    ok, new_qty = tool_set_cart_qty(state, product_id, target_qty)
    if not ok:
        state.assistant_message = (
            "No he podido actualizar la cantidad."
            if lang == "es"
            else "I couldn't update the quantity."
        )
        return state

    total = tool_cart_total(state)

    state.mode = Mode.CART
    state.ui_product = product
    state.ui_products = []
    state.ui_cart_total = total

    state.last_cart_product_ids = [product_id]
    state.last_cart_op = "set_qty"
    state.last_cart_qty = new_qty

    state.assistant_message = (
        f"Perfecto ✅ Dejé [{product.id}] {product.brand} - {product.name} en {new_qty} unidad(es).\n\nTotal: €{total:.2f}"
        if lang == "es"
        else f"Done ✅ Set [{product.id}] {product.brand} - {product.name} to {new_qty} unit(s).\n\nTotal: €{total:.2f}"
    )

    return state
