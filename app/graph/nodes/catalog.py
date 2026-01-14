from __future__ import annotations

import re

from app.engine.state import ConversationState
from app.tools import tool_list_catalog, tool_get_product, tool_find_products_by_name
from app.ux import t


def show_catalog_node(state: ConversationState) -> ConversationState:
    """
    List the available perfumes in the catalog.

    Single responsibility:
    - Load catalog data.
    - Format a chat-friendly list.
    """
    catalog = tool_list_catalog()
    state.ui_products = catalog
    state.ui_product = None
    state.ui_cart_total = None

    lines: list[str] = [t(state, "catalog_header")]
    for p in catalog:
        brand = f"{p.brand} - " if p.brand else ""
        size = f" {p.size_ml}ml" if p.size_ml else ""
        conc = f" ({p.concentration})" if p.concentration else ""
        lines.append(f"- [{p.id}] {brand}{p.name}{conc}{size} — €{p.price:.2f}")

    lines.append("")
    next_line = t(state, "catalog_next")
    if next_line:
        lines.append(next_line)

    state.assistant_message = "\n".join(lines)
    return state


def show_product_detail_node(state: ConversationState) -> ConversationState:
    """
    Show detailed information for a selected product.

    Supports:
    - by ID (301)
    - by name/brand query (e.g. "Show me Flowerbomb", "Enséñame Dolce & Gabbana")
    """
    msg = state.user_message or ""

    # 1) Try ID first
    match = re.search(r"\b(\d{3})\b", msg)
    product_id: int | None = int(match.group(1)) if match else None

    # 2) If no ID, try name search
    if product_id is None:
        matches = tool_find_products_by_name(msg)

        if len(matches) == 1:
            product_id = matches[0]

        elif len(matches) > 1:
            state.candidate_products = matches
            state.pending_product_op = "detail"

            lines = [t(state, "detail_multiple_found")]
            for i, pid in enumerate(matches, start=1):
                p = tool_get_product(pid)
                if p:
                    lines.append(f"{i}) [{p.id}] {p.brand} - {p.name}")

            lines.append(t(state, "detail_multiple_reply_hint"))
            state.assistant_message = "\n".join(lines)
            return state

        else:
            state.assistant_message = t(state, "detail_not_found_by_name")
            return state

    product = tool_get_product(product_id)
    state.ui_product = product
    state.ui_products = []
    state.ui_cart_total = None

    if not product:
        state.assistant_message = t(state, "product_not_found", product_id=product_id)
        return state

    state.selected_product_id = product.id
    product_label = f"[{product.id}] {product.brand} - {product.name}"

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

    lang = (state.preferred_language or "en").lower()

    # ✅ descripción según idioma + fallback
    if lang == "es":
        desc = product.description_es or product.description
    else:
        desc = product.description or product.description_es

    if desc:
        lines.append(t(state, "product_description", value=desc))

    lines.append("")
    next_line = t(state, "product_details_next")
    if next_line:
        lines.append(next_line)

    state.assistant_message = "\n".join(lines)
    return state
