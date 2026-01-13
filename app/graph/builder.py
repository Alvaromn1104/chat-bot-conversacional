from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.engine.state import ConversationState

from app.graph.routing.selectors import route_node, select_next_node
from app.graph.nodes import (
    echo_node,
    show_catalog_node,
    show_product_detail_node,
    add_to_cart_node,
    view_cart_node,
    remove_from_cart_node,
    checkout_confirm_node,
    handle_checkout_confirmation_node,
    handle_checkout_review_node,
    collect_shipping_node,
    recommend_product_node,
    interpret_user_node,
    bulk_cart_update_node,
    resolve_product_choice_node,
    adjust_cart_qty_node,
)


def build_graph():
    g = StateGraph(ConversationState)

    g.add_node("interpret_user", interpret_user_node)
    g.add_node("route", route_node)
    g.add_node("show_catalog", show_catalog_node)
    g.add_node("show_product_detail", show_product_detail_node)
    g.add_node("add_to_cart", add_to_cart_node)
    g.add_node("view_cart", view_cart_node)
    g.add_node("remove_from_cart", remove_from_cart_node)
    g.add_node("bulk_cart_update", bulk_cart_update_node)
    g.add_node("resolve_product_choice", resolve_product_choice_node)

    g.add_node("adjust_cart_qty", adjust_cart_qty_node)

    g.add_node("checkout_confirm", checkout_confirm_node)
    g.add_node("handle_checkout_confirmation", handle_checkout_confirmation_node)
    g.add_node("handle_checkout_review", handle_checkout_review_node)  # ✅ NEW
    g.add_node("collect_shipping", collect_shipping_node)

    g.add_node("recommend_product", recommend_product_node)

    g.add_node("echo", echo_node)

    g.set_entry_point("interpret_user")
    g.add_edge("interpret_user", "route")

    g.add_conditional_edges(
        "route",
        select_next_node,
        {
            "show_catalog": "show_catalog",
            "show_product_detail": "show_product_detail",
            "add_to_cart": "add_to_cart",
            "view_cart": "view_cart",
            "remove_from_cart": "remove_from_cart",
            "checkout_confirm": "checkout_confirm",
            "handle_checkout_confirmation": "handle_checkout_confirmation",
            "handle_checkout_review": "handle_checkout_review",  # ✅ NEW
            "collect_shipping": "collect_shipping",
            "recommend_product": "recommend_product",
            "bulk_cart_update": "bulk_cart_update",
            "resolve_product_choice": "resolve_product_choice",
            "adjust_cart_qty": "adjust_cart_qty",
            "echo": "echo",
        },
    )

    g.add_edge("show_catalog", END)
    g.add_edge("show_product_detail", END)
    g.add_edge("resolve_product_choice", END)
    g.add_edge("add_to_cart", END)
    g.add_edge("view_cart", END)
    g.add_edge("remove_from_cart", END)
    g.add_edge("bulk_cart_update", END)

    g.add_edge("adjust_cart_qty", END)

    g.add_edge("checkout_confirm", END)
    g.add_edge("handle_checkout_confirmation", END)
    g.add_edge("handle_checkout_review", END)  # ✅ NEW
    g.add_edge("collect_shipping", END)

    g.add_edge("recommend_product", END)

    g.add_edge("echo", END)

    return g.compile()
