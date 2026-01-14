from __future__ import annotations

import re
from typing import Optional

from app.engine.state import ConversationState, Mode
from app.tools import (
    tool_get_product,
    tool_add_to_cart,
    tool_remove_from_cart,
    tool_set_cart_qty,
    tool_cart_total,
)
from app.ux import t


def _norm(text: str | None) -> str:
    return (text or "").strip().casefold()


def _parse_choice(text: str) -> Optional[int]:
    tt = _norm(text)

    m = re.search(r"\b(\d{3})\b", tt)
    if m:
        return int(m.group(1))

    m2 = re.search(r"\b(\d+)\b", tt)
    if m2:
        return int(m2.group(1))

    return None


def _pick_candidate_by_text(text: str, candidate_ids: list[int]) -> Optional[int]:
    q = _norm(text)
    if not q:
        return None

    tokens = [x for x in re.split(r"\s+", q) if x]
    if not tokens:
        return None

    scored: list[tuple[int, int]] = []
    for pid in candidate_ids:
        p = tool_get_product(pid)
        if not p:
            continue
        hay = f"{p.brand or ''} {p.name}".casefold()
        score = sum(1 for tok in tokens if tok in hay)
        if score > 0:
            scored.append((score, pid))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score = scored[0][0]
    best = [pid for s, pid in scored if s == best_score]

    return best[0] if len(best) == 1 else None


def _get_description_for_lang(state: ConversationState, product) -> str | None:
    lang = (state.preferred_language or "en").lower()
    if lang == "es":
        return getattr(product, "description_es", None) or getattr(product, "description", None)
    return getattr(product, "description", None) or getattr(product, "description_es", None)


def resolve_product_choice_node(state: ConversationState) -> ConversationState:
    candidates = state.candidate_products or []
    op = state.pending_product_op
    qty = state.pending_qty or 1

    if not candidates or not op:
        state.assistant_message = t(state, "fallback_ok")
        return state

    choice = _parse_choice(state.user_message)

    if choice is None:
        picked = _pick_candidate_by_text(state.user_message, candidates)
        if picked is None:
            # ✅ UX: lista opciones SIEMPRE cuando hay ambigüedad
            header_key = {
                "add": "multiple_matches_which_add",
                "remove": "multiple_matches_which_remove",
                "set_qty": "multiple_matches_which_adjust",
                "detail": "detail_multiple_found",
            }.get(op, "clarify_pick_one")

            lines = [t(state, header_key)]
            for i, pid in enumerate(candidates, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")

            # copy final según operación (ya los tienes definidos)
            if op == "detail":
                lines.append(t(state, "detail_multiple_reply_hint"))
            elif op == "add":
                lines.append(t(state, "reply_number_id_name"))
            else:
                lines.append(t(state, "reply_number_id"))

            state.assistant_message = "\n".join(lines)
            return state

        choice = picked

    # choice as product id vs option number
    if 100 <= choice <= 999:
        if choice not in candidates:
            state.assistant_message = t(state, "clarify_id_not_in_options")
            return state
        product_id = choice
    else:
        idx = choice - 1
        if idx < 0 or idx >= len(candidates):
            state.assistant_message = t(state, "clarify_invalid_number")
            return state
        product_id = candidates[idx]

    product = tool_get_product(product_id)
    if not product:
        state.assistant_message = t(state, "product_not_found", product_id=product_id)
        return state

    # 🔥 limpiar estado de clarificación (antes de responder)
    state.candidate_products = []
    state.pending_product_op = None
    state.pending_qty = None

    # ✅ mantener “contexto activo” del producto para siguientes turnos tipo "añade 2" / "quítame 1"
    state.selected_product_id = product.id

    product_label = f"[{product.id}] {product.brand} - {product.name}"

    # ===============================
    # detail
    # ===============================
    if op == "detail":
        state.mode = Mode.CATALOG
        state.ui_product = product
        state.ui_products = []
        state.ui_cart_total = None

        lines = [
            t(state, "product_details_header", product_label=product_label),
            t(state, "product_price", price=product.price),
        ]

        if product.concentration:
            lines.append(t(state, "product_concentration", value=product.concentration))
        if product.size_ml:
            lines.append(t(state, "product_size", value=product.size_ml))
        if product.family:
            lines.append(t(state, "product_family", value=product.family))

        desc = _get_description_for_lang(state, product)
        if desc:
            lines.append(t(state, "product_description", value=desc))

        lines.append("")
        lines.append(t(state, "clarify_detail_next"))

        state.assistant_message = "\n".join(lines)
        return state

    # ===============================
    # add / remove / set_qty
    # ===============================
    if op == "add":
        ok, added = tool_add_to_cart(state, product_id, qty)
        if not ok:
            state.assistant_message = t(state, "add_no_stock", product_label=product_label)
            return state

        total = tool_cart_total(state)
        state.mode = Mode.CART
        state.ui_cart_total = total

        # ✅ contexto para próximos turnos
        state.last_cart_product_ids = [product_id]
        state.last_cart_op = "add"
        state.last_cart_qty = added

        state.assistant_message = t(
            state,
            "clarify_added",
            product_label=product_label,
            qty=added,
            total=total,
        )
        return state

    if op == "remove":
        ok, removed = tool_remove_from_cart(state, product_id, qty)
        if not ok:
            state.assistant_message = t(state, "clarify_not_in_cart")
            return state

        total = tool_cart_total(state)
        state.mode = Mode.CART
        state.ui_cart_total = total

        # ✅ contexto para próximos turnos
        state.last_cart_product_ids = [product_id]
        state.last_cart_op = "remove"
        state.last_cart_qty = removed

        state.assistant_message = t(
            state,
            "clarify_removed",
            product_label=product_label,
            qty=removed,
            total=total,
        )
        return state

    if op == "set_qty":
        ok, new_qty = tool_set_cart_qty(state, product_id, qty)
        if not ok:
            state.assistant_message = t(state, "clarify_set_qty_failed")
            return state

        total = tool_cart_total(state)
        state.mode = Mode.CART
        state.ui_cart_total = total

        # ✅ contexto para próximos turnos
        state.last_cart_product_ids = [product_id]
        state.last_cart_op = "set_qty"
        state.last_cart_qty = new_qty

        state.assistant_message = t(
            state,
            "clarify_qty_updated",
            product_label=product_label,
            qty=new_qty,
            total=total,
        )
        return state

    state.assistant_message = t(state, "fallback_ok")
    return state
