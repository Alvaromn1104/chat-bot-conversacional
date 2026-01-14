from __future__ import annotations

from typing import Callable

from app.engine.state import ConversationState

from .checkout_rules import rule_exit, rule_mode_guardrails, rule_checkout
from .language_rules import rule_language_detection
from .cart_bulk_rules import rule_pending_bulk, rule_bulk_cart_names
from .product_detail_rules import (
    rule_pending_product,
    rule_product_detail_by_id,
    rule_product_detail_by_name,
)
from .recommend_rules import apply_recommend_heuristic
from .catalog_rules import rule_show_catalog
from .help_rules import rule_help
from .cart_single_rules import (
    rule_adjust_qty,
    rule_single_cart_command,
    rule_implicit_cart_op,
    rule_view_cart,
    rule_cart_commands_any,
    rule_remove_qty_only_needs_disambiguation,
)
from .out_of_scope_rules import rule_out_of_scope


Rule = Callable[[ConversationState], bool]
"""
A routing rule that inspects the current ConversationState.

Each rule:
- returns True if it handled the state and routing should stop
- returns False to allow evaluation of the next rule
"""


# Ordered list of routing rules.
#
# IMPORTANT:
# - Rules are evaluated sequentially.
# - The first rule returning True wins and stops further evaluation.
# - Order matters and reflects priority (exit/guardrails first, fallbacks last).
#
# This approach keeps routing deterministic and avoids unnecessary LLM calls.
RULES: list[Rule] = [
    # --- Hard stops / global guards ---
    rule_exit,
    rule_language_detection,
    rule_pending_bulk,
    rule_pending_product,
    rule_mode_guardrails,

    # --- Checkout-related rules ---
    rule_checkout,

    # --- Recommendation heuristics ---
    apply_recommend_heuristic,

    # --- Catalog / help ---
    rule_show_catalog,
    rule_help,

    # --- Cart disambiguation and commands ---
    rule_remove_qty_only_needs_disambiguation,
    rule_bulk_cart_names,
    rule_single_cart_command,
    rule_adjust_qty,
    rule_implicit_cart_op,
    rule_view_cart,

    # --- Product detail ---
    rule_product_detail_by_id,
    rule_product_detail_by_name,

    # --- Fallbacks ---
    rule_cart_commands_any,
    rule_out_of_scope,
]
