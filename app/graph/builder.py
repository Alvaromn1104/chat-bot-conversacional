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
    recommend_product_node,
    interpret_user_node,
    bulk_cart_update_node,
    resolve_product_choice_node,
    adjust_cart_qty_node,
)


def build_graph():
    """
    Build and compile the LangGraph state machine.

    Design notes:
    - One user turn triggers a single graph execution.
    - `interpret_user` updates the state from the raw user message (intent/entities).
    - `route` selects the next node via `select_next_node`.
    - All business/UI nodes end the turn by transitioning to END.
    """
    g = StateGraph(ConversationState)

    # 1) Parse/interpret the user message into structured state.
    g.add_node("interpret_user", interpret_user_node)

    # 2) Route to the appropriate node based on the updated state.
    g.add_node("route", route_node)

    # Catalog / product browsing
    g.add_node("show_catalog", show_catalog_node)
    g.add_node("show_product_detail", show_product_detail_node)

    # Cart operations
    g.add_node("add_to_cart", add_to_cart_node)
    g.add_node("view_cart", view_cart_node)
    g.add_node("remove_from_cart", remove_from_cart_node)
    g.add_node("bulk_cart_update", bulk_cart_update_node)
    g.add_node("resolve_product_choice", resolve_product_choice_node)
    g.add_node("adjust_cart_qty", adjust_cart_qty_node)

    # Checkout flow
    g.add_node("checkout_confirm", checkout_confirm_node)
    g.add_node("handle_checkout_confirmation", handle_checkout_confirmation_node)
    g.add_node("handle_checkout_review", handle_checkout_review_node)

    # Recommendations / fallback
    g.add_node("recommend_product", recommend_product_node)
    g.add_node("echo", echo_node)

    # Entry point for every turn.
    g.set_entry_point("interpret_user")
    g.add_edge("interpret_user", "route")

    # Contract: `select_next_node` must return one of the keys in this mapping.
    g.add_conditional_edges(
        "route",
        select_next_node,
        {
            "show_catalog": "show_catalog",
            "show_product_detail": "show_product_detail",
            "add_to_cart": "add_to_cart",
            "view_cart": "view_cart",
            "remove_from_cart": "remove_from_cart",
            "bulk_cart_update": "bulk_cart_update",
            "resolve_product_choice": "resolve_product_choice",
            "adjust_cart_qty": "adjust_cart_qty",
            "checkout_confirm": "checkout_confirm",
            "handle_checkout_confirmation": "handle_checkout_confirmation",
            "handle_checkout_review": "handle_checkout_review",
            "recommend_product": "recommend_product",
            "echo": "echo",
        },
    )

    # End the graph after executing a single business/UI node per turn.
    for node in [
        "show_catalog",
        "show_product_detail",
        "resolve_product_choice",
        "add_to_cart",
        "view_cart",
        "remove_from_cart",
        "bulk_cart_update",
        "adjust_cart_qty",
        "checkout_confirm",
        "handle_checkout_confirmation",
        "handle_checkout_review",
        "recommend_product",
        "echo",
    ]:
        g.add_edge(node, END)

    return g.compile()
