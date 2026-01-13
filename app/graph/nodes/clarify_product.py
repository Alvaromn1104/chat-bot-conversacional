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


def _parse_choice(text: str) -> Optional[int]:
    t = (text or "").strip().lower()

    m = re.search(r"\b(\d{3})\b", t)
    if m:
        return int(m.group(1))

    m2 = re.search(r"\b(\d+)\b", t)
    if m2:
        return int(m2.group(1))

    return None


def _pick_candidate_by_text(text: str, candidate_ids: list[int]) -> Optional[int]:
    q = (text or "").lower().strip()
    if not q:
        return None

    tokens = [t for t in re.split(r"\s+", q) if t]
    if not tokens:
        return None

    scored: list[tuple[int, int]] = []
    for pid in candidate_ids:
        p = tool_get_product(pid)
        if not p:
            continue
        hay = f"{p.brand or ''} {p.name}".lower()
        score = sum(1 for tok in tokens if tok in hay)
        if score > 0:
            scored.append((score, pid))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score = scored[0][0]
    best = [pid for s, pid in scored if s == best_score]

    return best[0] if len(best) == 1 else None


def resolve_product_choice_node(state: ConversationState) -> ConversationState:
    lang = state.preferred_language or "en"
    candidates = state.candidate_products or []
    op = state.pending_product_op
    qty = state.pending_qty or 1

    if not candidates or not op:
        state.assistant_message = "Vale." if lang == "es" else "Okay."
        return state

    choice = _parse_choice(state.user_message)

    if choice is None:
        picked = _pick_candidate_by_text(state.user_message, candidates)
        if picked is None:
            state.assistant_message = (
                "¿Cuál quieres? Responde con el número, el ID o el nombre."
                if lang == "es"
                else "Which one do you want? Reply with the number, ID, or name."
            )
            return state
        choice = picked

    if 100 <= choice <= 999:
        if choice not in candidates:
            state.assistant_message = (
                "Ese ID no está entre las opciones."
                if lang == "es"
                else "That ID is not among the options."
            )
            return state
        product_id = choice
    else:
        idx = choice - 1
        if idx < 0 or idx >= len(candidates):
            state.assistant_message = (
                "Ese número no es válido."
                if lang == "es"
                else "That number is invalid."
            )
            return state
        product_id = candidates[idx]

    product = tool_get_product(product_id)
    if not product:
        state.assistant_message = (
            f"No encuentro el producto {product_id}."
            if lang == "es"
            else f"I couldn't find product {product_id}."
        )
        return state

    # 🔥 LIMPIEZA DE ESTADO (MUY IMPORTANTE)
    state.candidate_products = []
    state.pending_product_op = None
    state.pending_qty = None

    # ===============================
    # 🆕 NUEVO: DETALLE DE PRODUCTO
    # ===============================
    if op == "detail":
        state.mode = Mode.CATALOG
        state.selected_product_id = product.id
        state.ui_product = product
        state.ui_products = []
        state.ui_cart_total = None

        lines = [
            f"Detalles del producto [{product.id}] {product.brand} - {product.name}:"
            if lang == "es"
            else f"Product details for [{product.id}] {product.brand} - {product.name}:",
            f"- Precio: €{product.price:.2f}"
            if lang == "es"
            else f"- Price: €{product.price:.2f}",
        ]

        if product.concentration:
            lines.append(
                f"- Concentración: {product.concentration}"
                if lang == "es"
                else f"- Concentration: {product.concentration}"
            )
        if product.size_ml:
            lines.append(
                f"- Tamaño: {product.size_ml} ml"
                if lang == "es"
                else f"- Size: {product.size_ml} ml"
            )
        if product.family:
            lines.append(
                f"- Familia olfativa: {product.family}"
                if lang == "es"
                else f"- Olfactory family: {product.family}"
            )
        if product.description:
            lines.append(
                f"- Descripción: {product.description}"
                if lang == "es"
                else f"- Description: {product.description}"
            )

        lines.append("")
        lines.append(
            'Puedes decir: "Añádelo al carrito" o "Volver al catálogo".'
            if lang == "es"
            else 'You can say: "Add it to the cart" or "Back to catalog".'
        )

        state.assistant_message = "\n".join(lines)
        return state

    # ===============================
    # RESTO: add / remove / set_qty
    # ===============================
    if op == "add":
        ok, added = tool_add_to_cart(state, product_id, qty)
        if not ok:
            state.assistant_message = "Sin stock."
            return state

        total = tool_cart_total(state)
        state.mode = Mode.CART
        state.assistant_message = (
            f"Añadido ✅ [{product.id}] {product.name} x{added}\nTotal: €{total:.2f}"
            if lang == "es"
            else f"Added ✅ [{product.id}] {product.name} x{added}\nTotal: €{total:.2f}"
        )
        return state

    if op == "remove":
        ok, removed = tool_remove_from_cart(state, product_id, qty)
        if not ok:
            state.assistant_message = "No estaba en el carrito."
            return state

        total = tool_cart_total(state)
        state.mode = Mode.CART
        state.assistant_message = (
            f"Quitado ✅ [{product.id}] {product.name}\nTotal: €{total:.2f}"
            if lang == "es"
            else f"Removed ✅ [{product.id}] {product.name}\nTotal: €{total:.2f}"
        )
        return state

    if op == "set_qty":
        ok, new_qty = tool_set_cart_qty(state, product_id, qty)
        if not ok:
            state.assistant_message = "No pude actualizar la cantidad."
            return state

        total = tool_cart_total(state)
        state.mode = Mode.CART
        state.assistant_message = (
            f"Cantidad actualizada ✅ [{product.id}] x{new_qty}\nTotal: €{total:.2f}"
            if lang == "es"
            else f"Quantity updated ✅ [{product.id}] x{new_qty}\nTotal: €{total:.2f}"
        )
        return state

    state.assistant_message = "Vale." if lang == "es" else "Okay."
    return state
