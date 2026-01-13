from __future__ import annotations

import inspect
import logging

from app.engine.state import ConversationState
from app.tools import tool_recommend_products, tool_list_catalog
from app.ux import t

logger = logging.getLogger("app.graph.nodes.recommend")


def recommend_product_node(state: ConversationState) -> ConversationState:

    

    families = getattr(state, "recommended_family", None) or []
    audience = getattr(state, "recommended_audience", None)
    min_price = getattr(state, "recommended_min_price", None)
    max_price = getattr(state, "recommended_max_price", None)

    logger = logging.getLogger("app.graph.nodes.recommend")

    logger.info("recommend_product_node file=%r", inspect.getsourcefile(recommend_product_node))
    logger.info("slots families=%r audience=%r min=%r max=%r",
            families, audience, min_price, max_price)
    if not families and audience is None and min_price is None and max_price is None:
        # No inventamos: pedimos aclaración
        state.assistant_message = (
            "¿Qué estilo de perfume quieres (cítrico, amaderado, floral, oriental…)? "
            "¿Y tu presupuesto?"
            if (state.preferred_language or "en") == "es"
            else "What style do you want (woody, citrus, floral, oriental…)? And what's your budget?"
        )
        state.ui_products = []
        state.ui_product = None
        state.ui_cart_total = None
        return state

    logger.info(
        "RECOMMEND slots families=%r audience=%r min_price=%r max_price=%r",
        families, audience, min_price, max_price,
    )
    logger.info("recommend_product_node file=%r", inspect.getsourcefile(recommend_product_node))
    logger.info("tool_recommend_products file=%r", inspect.getsourcefile(tool_recommend_products))

    catalog = tool_list_catalog()
    
    products = tool_recommend_products(
        families=families,
        audience=audience,
        min_price=min_price,
        max_price=max_price,
        limit=len(catalog),  # ✅ sin límite
    )

    # ✅ Si no hay resultados, no inventamos: explicamos y listamos lo que sí hay de esa(s) familia(s)
    if not products:
        norm_families = [(f or "").strip().lower() for f in families if (f or "").strip()]

        def _family_ok(p) -> bool:
            if not norm_families:
                return True
            return (p.family or "").strip().lower() in norm_families

        available_same_family = [p for p in catalog if _family_ok(p)]

        family_label = " o ".join(families) if families else "esa familia"
        if (state.preferred_language or "en") == "es":
            if available_same_family:
                lines = [
                    f"No tenemos perfumes {family_label} en ese rango de precio.",
                    "",
                    f"Pero sí tenemos estos perfumes {family_label}:",
                ]
            else:
                lines = [f"No tenemos perfumes de la familia {family_label}."]
        else:
            if available_same_family:
                lines = [
                    f"We don't have {family_label} perfumes in that price range.",
                    "",
                    f"But we do have these {family_label} perfumes:",
                ]
            else:
                lines = [f"We don't have perfumes in the {family_label} family."]

        # ✅ ANTES: [:10]  ->  ahora: TODOS
        for p in sorted(available_same_family, key=lambda x: x.price):
            brand = f"{p.brand} - " if p.brand else ""
            lines.append(f"- [{p.id}] {brand}{p.name} — €{p.price:.2f}")

        # ✅ ANTES: available_same_family[:10]  ->  ahora: TODOS
        state.ui_products = available_same_family
        state.ui_product = None
        state.ui_cart_total = None
        state.assistant_message = "\n".join(lines)
        return state

    # ✅ Blindaje extra (no debería hacer falta, pero no molesta)
    if min_price is not None:
        products = [p for p in products if p.price >= min_price]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]

    # ✅ AÑADIDO MÍNIMO: dejar “contexto” para "añádelo"
    if products:
        state.selected_product_id = products[0].id

    state.ui_products = products
    state.ui_product = None
    state.ui_cart_total = None

    lines: list[str] = [t(state, "recommend_header")]
    for p in products:
        brand = f"{p.brand} - " if p.brand else ""
        lines.append(f"- [{p.id}] {brand}{p.name} — €{p.price:.2f}")

    lines.append("")
    lines.append(t(state, "recommend_next"))

    state.assistant_message = "\n".join(lines)
    state.pending_recommend_clarification = False
    state.recommended_family = None
    state.recommended_audience = None
    state.recommended_min_price = None
    state.recommended_max_price = None  
    return state
