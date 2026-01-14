from __future__ import annotations

import re

from app.engine.state import ConversationState, Mode
from app.ux import t
from .common_rules import CHECKOUT_RE, msg_l


def rule_exit(state: ConversationState) -> bool:
    """
    Detect explicit conversation exit intent (ES/EN) and terminate the session.

    Note: checkout phrases (e.g., "finalizar compra") are explicitly excluded
    to avoid treating transactional intents as a session exit.
    """
    text = msg_l(state)

    # If the message looks like a checkout intent, it is not treated as an exit.
    if CHECKOUT_RE.search(text):
        return False

    # Common exit keywords in ES/EN.
    EXIT_KEYWORDS = {
        "salir", "terminar", "finalizar", "cerrar", "fin",
        "exit", "end", "quit", "bye", "adiós", "adios",
    }

    if any(re.search(rf"\b{k}\b", text) for k in EXIT_KEYWORDS):
        state.mode = Mode.END
        state.should_end = True
        state.assistant_message = t(state, "ended")
        return True

    return False


def rule_mode_guardrails(state: ConversationState) -> bool:
    """
    Enforce mode-based routing to keep the flow consistent across turns.

    When a mode implies a specific next step (e.g., checkout confirmation),
    route directly to the appropriate node.
    """
    if state.mode == Mode.CHECKOUT_CONFIRM:
        state.next_node = "handle_checkout_confirmation"
        return True

    if state.mode == Mode.CHECKOUT_REVIEW:
        state.next_node = "handle_checkout_review"
        return True

    if state.mode == Mode.COLLECT_SHIPPING:
        # Shipping data is collected via UI form; keep it open and remind the user.
        state.ui_show_checkout_form = True
        state.assistant_message = t(state, "checkout_form_open_reminder")
        state.next_node = "echo"
        return True

    return False


def rule_checkout(state: ConversationState) -> bool:
    """
    Detect checkout intent and route the user to the checkout confirmation step.
    """
    msg = (state.user_message or "").strip().lower()
    if msg and CHECKOUT_RE.search(msg):
        state.next_node = "checkout_confirm"
        return True
    return False
