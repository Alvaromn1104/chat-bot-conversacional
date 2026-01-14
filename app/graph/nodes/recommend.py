from __future__ import annotations

import logging

from app.engine.state import ConversationState
from app.tools import tool_recommend_products, tool_list_catalog
from app.ux import t

logger = logging.getLogger("app.graph.nodes.recommend")


def recommend_product_node(state: ConversationState) -> ConversationState:
    families = state.recommended_family or []
    audience = state.recommended_audience
    min_price = state.recommended_min_price
    max_price = state.recommended_max_price

    logger.info(
        "RECOMMEND session=%s mode=%s families=%r audience=%r min=%r max=%r cart_size=%d",
        state.session_id,
        getattr(state.mode, "value", state.mode),
        families,
        audience,
        min_price,
        max_price,
        len(state.cart),
    )

    # 0) No inventar: pedir aclaración
    if not families and audience is None and min_price is None and max_price is None:
        state.assistant_message = t(state, "recommend_clarify")
        state.ui_products = []
        state.ui_product = None
        state.ui_cart_total = None
        return state

    catalog = tool_list_catalog()

    products = tool_recommend_products(
        families=families,
        audience=audience,
        min_price=min_price,
        max_price=max_price,
        limit=len(catalog),  # sin límite
    )

    # 1) No resultados: explicar y listar lo disponible de esa familia
    if not products:
        norm_families = [(f or "").strip().lower() for f in families if (f or "").strip()]

        def _family_ok(p) -> bool:
            if not norm_families:
                return True
            return (p.family or "").strip().lower() in norm_families

        available_same_family = [p for p in catalog if _family_ok(p)]

        family_label = " o ".join(families) if families else t(state, "family_generic_label")

        if available_same_family:
            lines = [
                t(state, "recommend_no_results_in_price", family_label=family_label),
                "",
                t(state, "recommend_but_have_family", family_label=family_label),
            ]
        else:
            lines = [t(state, "recommend_no_family", family_label=family_label)]

        for p in sorted(available_same_family, key=lambda x: x.price):
            brand = f"{p.brand} - " if p.brand else ""
            lines.append(t(
                state,
                "catalog_item",
                product_id=p.id,
                brand=brand,
                name=p.name,
                price=p.price,
            ))

        state.ui_products = available_same_family
        state.ui_product = None
        state.ui_cart_total = None
        state.assistant_message = "\n".join(lines)
        return state

    # 2) Blindaje extra
    if min_price is not None:
        products = [p for p in products if p.price >= min_price]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]

    # Contexto para "añádelo"
    if products:
        state.selected_product_id = products[0].id

    state.ui_products = products
    state.ui_product = None
    state.ui_cart_total = None

    lines: list[str] = [t(state, "recommend_header")]
    for p in products:
        brand = f"{p.brand} - " if p.brand else ""
        lines.append(t(
            state,
            "catalog_item",
            product_id=p.id,
            brand=brand,
            name=p.name,
            price=p.price,
        ))

    lines.append("")
    lines.append(t(state, "recommend_next"))

    state.assistant_message = "\n".join(lines)

    # limpiar slots
    state.pending_recommend_clarification = False
    state.recommended_family = None
    state.recommended_audience = None
    state.recommended_min_price = None
    state.recommended_max_price = None

    return state
