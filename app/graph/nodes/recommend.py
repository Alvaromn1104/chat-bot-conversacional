from __future__ import annotations

from app.engine.state import ConversationState
from app.tools import tool_recommend_products, tool_list_catalog
from app.ux import t


def recommend_product_node(state: ConversationState) -> ConversationState:
    """
    Recommend products based on extracted user preferences.

    This node applies deterministic filtering logic and never invents
    products or prices. If the information provided by the user is
    insufficient, it asks for clarification.
    """
    families = state.recommended_family or []
    audience = state.recommended_audience
    min_price = state.recommended_min_price
    max_price = state.recommended_max_price

    # 0) Not enough information → ask for clarification
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
        limit=len(catalog),  # no artificial limit
    )

    # 1) No results → explain and show what exists in that family
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
            lines.append(
                t(
                    state,
                    "catalog_item",
                    product_id=p.id,
                    brand=brand,
                    name=p.name,
                    price=p.price,
                )
            )

        state.ui_products = available_same_family
        state.ui_product = None
        state.ui_cart_total = None
        state.assistant_message = "\n".join(lines)
        return state

    # 2) Extra safety filter
    if min_price is not None:
        products = [p for p in products if p.price >= min_price]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]

    # Context for follow-ups like "añádelo"
    if products:
        state.selected_product_id = products[0].id

    state.ui_products = products
    state.ui_product = None
    state.ui_cart_total = None

    lines = [t(state, "recommend_header")]
    for p in products:
        brand = f"{p.brand} - " if p.brand else ""
        lines.append(
            t(
                state,
                "catalog_item",
                product_id=p.id,
                brand=brand,
                name=p.name,
                price=p.price,
            )
        )

    lines.append("")
    lines.append(t(state, "recommend_next"))

    state.assistant_message = "\n".join(lines)

    # Clear recommendation context
    state.pending_recommend_clarification = False
    state.recommended_family = None
    state.recommended_audience = None
    state.recommended_min_price = None
    state.recommended_max_price = None

    return state
