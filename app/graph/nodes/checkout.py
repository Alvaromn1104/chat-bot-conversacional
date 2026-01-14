from __future__ import annotations

from app.engine.state import ConversationState, Mode
from app.ux import t

# Shared yes/no vocabulary (ES + EN).
_YES = {
    "yes", "y", "sure", "ok", "okay", "continue", "confirm",
    "sí", "si", "s", "vale", "venga", "continuar", "confirmar",
}
_NO = {"no", "n", "cancel", "stop", "cancela", "cancelar", "parar"}


def _norm(text: str | None) -> str:
    """Normalize user input for robust matching (case-insensitive, trimmed)."""
    return (text or "").strip().casefold()


def _is_yes(user_text: str) -> bool:
    """Return True if the normalized input is an affirmative answer."""
    return user_text in _YES


def _is_no(user_text: str) -> bool:
    """Return True if the normalized input is a negative answer."""
    return user_text in _NO


def checkout_confirm_node(state: ConversationState) -> ConversationState:
    """
    Start checkout by asking the user to confirm the purchase.

    Guardrails:
    - If the cart is empty, prevent checkout from starting.
    """
    if not state.cart:
        state.assistant_message = t(state, "cart_empty")
        return state

    state.mode = Mode.CHECKOUT_CONFIRM
    state.assistant_message = t(state, "checkout_confirm")
    return state


def handle_checkout_confirmation_node(state: ConversationState) -> ConversationState:
    """
    Handle the yes/no confirmation step before opening the shipping form (UI popup).
    """
    user_text = _norm(state.user_message)

    if _is_yes(user_text):
        state.ui_form_error = None
        state.ui_show_checkout_form = True

        state.assistant_message = t(state, "checkout_open_form")
        state.mode = Mode.COLLECT_SHIPPING
        return state

    if _is_no(user_text):
        state.mode = Mode.CART
        state.ui_show_checkout_form = False
        state.ui_form_error = None
        state.assistant_message = t(state, "checkout_cancelled")
        return state

    state.assistant_message = t(state, "checkout_ask_yesno")
    return state


def handle_checkout_review_node(state: ConversationState) -> ConversationState:
    """
    Final confirmation step after the shipping form has been submitted and reviewed.
    """
    user_text = _norm(state.user_message)

    if _is_yes(user_text):
        # Do not end the conversation automatically after checkout.
        state.should_end = False
        state.mode = Mode.CATALOG  # alternatively: Mode.CART

        # Simulate order completion: clear the cart.
        state.cart = []
        state.selected_product_id = None

        # Reset shipping info (kept in memory only).
        state.shipping.full_name = None
        state.shipping.address_line1 = None
        state.shipping.city = None
        state.shipping.postal_code = None
        state.shipping.phone = None

        # UI flags
        state.ui_show_checkout_form = False
        state.ui_form_error = None
        state.ui_cart_total = 0.0
        state.ui_product = None
        state.ui_products = []

        state.assistant_message = t(state, "checkout_confirmed")
        return state

    if _is_no(user_text):
        # User cancels after reviewing shipping details.
        state.shipping.full_name = None
        state.shipping.address_line1 = None
        state.shipping.city = None
        state.shipping.postal_code = None
        state.shipping.phone = None

        state.mode = Mode.CART
        state.ui_show_checkout_form = False
        state.ui_form_error = None

        state.assistant_message = t(state, "checkout_cancel_back_cart")
        return state

    state.assistant_message = t(state, "checkout_ask_yesno")
    return state


def collect_shipping_node(state: ConversationState) -> ConversationState:
    """
    Optional guardrail while the shipping form UI is open.

    If the user types in the chat instead of submitting the form, we remind them
    to complete the form to continue.
    """
    state.ui_show_checkout_form = True
    state.ui_form_error = None
    state.mode = Mode.COLLECT_SHIPPING

    state.assistant_message = t(state, "checkout_form_reminder")
    return state
