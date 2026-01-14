from __future__ import annotations

from app.engine.state import ConversationState, Mode
from app.ux import t

# ✅ Shared yes/no vocab (ES + EN)
_YES = {
    "yes", "y", "sure", "ok", "okay", "continue", "confirm",
    "sí", "si", "s", "vale", "venga", "continuar", "confirmar",
}
_NO = {"no", "n", "cancel", "stop", "cancela", "cancelar", "parar"}


def _norm(text: str | None) -> str:
    return (text or "").strip().casefold()


def _is_yes(user_text: str) -> bool:
    return user_text in _YES


def _is_no(user_text: str) -> bool:
    return user_text in _NO


def checkout_confirm_node(state: ConversationState) -> ConversationState:
    """
    Start checkout by asking for confirmation.
    """
    if not state.cart:
        state.assistant_message = t(state, "cart_empty")
        return state

    state.mode = Mode.CHECKOUT_CONFIRM
    state.assistant_message = t(state, "checkout_confirm")
    return state


def handle_checkout_confirmation_node(state: ConversationState) -> ConversationState:
    """
    Handle the yes/no confirmation before showing the checkout form (UI popup).
    """
    user_text = _norm(state.user_message)

    if _is_yes(user_text):
        state.ui_form_error = None
        state.ui_show_checkout_form = True
        state.assistant_message = t(state, "checkout_open_form")
        # ✅ El popup es un estado propio
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
    user_text = _norm(state.user_message)

    if _is_yes(user_text):
        # ✅ NO cerrar conversación automáticamente
        state.should_end = False
        state.mode = Mode.CATALOG  # o Mode.CART si prefieres volver al carrito

        # ✅ simular "pedido creado": limpiar carrito
        state.cart = []
        state.selected_product_id = None

        # opcional: limpiar shipping
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
    Guardrail mientras el formulario UI está abierto.
    Si el usuario escribe en el chat, le recordamos que complete el formulario.
    """
    state.ui_show_checkout_form = True
    state.ui_form_error = None
    state.mode = Mode.COLLECT_SHIPPING

    state.assistant_message = t(state, "checkout_form_reminder")
    return state
