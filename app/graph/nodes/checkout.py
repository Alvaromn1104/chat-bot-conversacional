from __future__ import annotations

from app.engine.state import ConversationState, Mode
from app.ux import t


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
    user_text = (state.user_message or "").strip().lower()

    yes = {"yes", "y", "sure", "ok", "okay", "continue", "sí", "si", "s", "vale", "venga", "continuar"}
    no = {"no", "n", "cancel", "stop", "cancela", "cancelar", "parar"}

    if user_text in yes:
        state.ui_form_error = None
        state.ui_show_checkout_form = True
        state.assistant_message = (
            "Perfecto ✅ Abro el formulario para tus datos de envío."
            if (state.preferred_language or "en") == "es"
            else "Perfect ✅ Opening the checkout form for your shipping details."
        )
        # ✅ CAMBIO CLAVE: el popup es un ESTADO propio
        state.mode = Mode.COLLECT_SHIPPING
        return state

    if user_text in no:
        state.mode = Mode.CART
        state.ui_show_checkout_form = False
        state.ui_form_error = None
        state.assistant_message = t(state, "checkout_cancelled")
        return state

    state.assistant_message = t(state, "checkout_ask_yesno")
    return state


def handle_checkout_review_node(state: ConversationState) -> ConversationState:
    user_text = (state.user_message or "").strip().lower()

    yes = {"yes", "y", "sure", "ok", "okay", "confirm", "sí", "si", "s", "vale", "venga", "confirmar"}
    no = {"no", "n", "cancel", "stop", "cancela", "cancelar", "parar"}

    if user_text in yes:
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

        if (state.preferred_language or "en") == "es":
            state.assistant_message = (
                "¡Pedido confirmado! ✅\n\n"
                "Gracias por tu compra 🙌\n"
                "¿Quieres ver el catálogo, recomendaciones o tu carrito?"
            )
        else:
            state.assistant_message = (
                "Order confirmed ✅\n\n"
                "Thanks for your purchase 🙌\n"
                "Do you want to see the catalog, recommendations, or your cart?"
            )
        return state

    if user_text in no:
        state.shipping.full_name = None
        state.shipping.address_line1 = None
        state.shipping.city = None
        state.shipping.postal_code = None
        state.shipping.phone = None

        state.mode = Mode.CART
        state.ui_show_checkout_form = False
        state.ui_form_error = None

        state.assistant_message = (
            "Vale 👍 He cancelado el pedido. Vuelves al carrito."
            if (state.preferred_language or "en") == "es"
            else "Okay 👍 I cancelled the order. Back to your cart."
        )
        return state

    state.assistant_message = (
        "Por favor, responde con 'sí' o 'no'."
        if (state.preferred_language or "en") == "es"
        else "Please reply with 'yes' or 'no'."
    )
    return state


def collect_shipping_node(state: ConversationState) -> ConversationState:
    """
    Handle checkout form submission (Gradio popup).
    """
    state.ui_show_checkout_form = False
    state.ui_form_error = None

    missing = []
    if not (state.shipping.full_name or "").strip():
        missing.append("full_name")
    if not (state.shipping.address_line1 or "").strip():
        missing.append("address_line1")
    if not (state.shipping.city or "").strip():
        missing.append("city")
    if not (state.shipping.postal_code or "").strip():
        missing.append("postal_code")
    if not (state.shipping.phone or "").strip():
        missing.append("phone")

    if missing:
        state.mode = Mode.COLLECT_SHIPPING
        state.ui_show_checkout_form = True

        if (state.preferred_language or "en") == "es":
            state.ui_form_error = "Faltan campos obligatorios. Revisa el formulario."
            state.assistant_message = "Ups 😅 faltan datos en el formulario. Por favor complétalo y vuelve a enviarlo."
        else:
            state.ui_form_error = "Missing required fields. Please review the form."
            state.assistant_message = "Oops 😅 some required fields are missing. Please complete the form and submit again."

        return state

    state.mode = Mode.CHECKOUT_REVIEW

    if (state.preferred_language or "en") == "es":
        state.assistant_message = (
            "Perfecto ✅ Aquí tienes el resumen del pedido:\n\n"
            f"- Nombre: {state.shipping.full_name}\n"
            f"- Dirección: {state.shipping.address_line1}\n"
            f"- Ciudad: {state.shipping.city}\n"
            f"- CP: {state.shipping.postal_code}\n"
            f"- Teléfono: {state.shipping.phone}\n\n"
            "¿Confirmas la compra? (sí/no)"
        )
    else:
        state.assistant_message = (
            "Perfect ✅ Here is your order summary:\n\n"
            f"- Name: {state.shipping.full_name}\n"
            f"- Address: {state.shipping.address_line1}\n"
            f"- City: {state.shipping.city}\n"
            f"- Postal code: {state.shipping.postal_code}\n"
            f"- Phone: {state.shipping.phone}\n\n"
            "Do you confirm the purchase? (yes/no)"
        )

    return state
