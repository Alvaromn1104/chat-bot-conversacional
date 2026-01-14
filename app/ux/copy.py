from __future__ import annotations

from typing import Any

from app.engine.state import ConversationState


_COPY: dict[str, dict[str, str]] = {
    "en": {
        # Generic
        "fallback_ok": "Okay.",
        "follow_up": "",
        "product_not_found": "I couldn't find product {product_id}.",
        "cart_empty": "Your cart is empty.",
        "need_product_id_add": 'Please tell me the product ID (e.g. "Add 301").',
        "need_product_id_remove": 'Please tell me the product ID (e.g. "Remove 302").',

        #Welcome / Ended (moved from ChatEngine)
        "welcome": (
            "Hi! 👋\n\n"
            "I’ll be your assistant while you browse our store.\n"
            "You can ask me to show the catalog, add perfumes to the cart, or get recommendations.\n\n"
            "How can I help you?"
        ),
        "ended": "Conversation ended. Thank you for visiting.",

        # Catalog / Product details / Recommend
        "catalog_header": "Available perfumes:",
        "catalog_next": "",
        "detail_multiple_found": "I found multiple matches. Which one do you want to view?",
        "detail_multiple_reply_hint": "Reply with the number, the ID, or the name.",
        "product_id_invalid": "Please specify a valid product ID.",
        "product_details_header": "Product details for {product_label}:",
        "product_price": "- Price: €{price:.2f}",
        "product_concentration": "- Concentration: {value}",
        "product_size": "- Size: {value} ml",
        "product_family": "- Olfactory family: {value}",
        "product_description": "- Description: {value}",
        "product_details_next": "",
        "recommend_need_clarification": "What style do you want (woody, citrus, floral, oriental…)? And what's your budget?",
        "recommend_no_results_in_price": "We don't have {family_label} perfumes in that price range.",
        "recommend_but_have_family": "But we do have these {family_label} perfumes:",
        "recommend_no_family": "We don't have perfumes in the {family_label} family.",
        "family_generic_label": "that family",
        "catalog_item": "- [{product_id}] {brand}{name} — €{price:.2f}",
        "recommend_header": "Recommended perfumes:",
        "recommend_next": "",
        "recommend_clarify": (
            "What kind of perfume do you want (woody, citrus, floral, oriental…)? "
            "Do you have a max budget? (e.g. 'woody under 100€')"
        ),
        "recommend_clarification_prompt": (
            "What kind of perfume do you want (woody, citrus, floral, oriental…)? "
            "Do you have a max budget? (e.g. 'woody under 100€')"
        ),

        "recommend_no_results_in_range": "We don't have {family_label} perfumes in that price range.",
        "recommend_no_family": "We don't have perfumes in the {family_label} family.",
        "recommend_but_have_these": "But we do have these {family_label} perfumes:",



        # Cart actions
        "add_ok": "Done ✅ I added {added} unit(s) of {product_label} to your cart{note}.",
        "add_no_stock": "Sorry — {product_label} is out of stock right now.",
        "remove_ok": "All set ✅ I removed {removed} unit(s) of {product_label} from your cart{note}.",
        "remove_not_in_cart": "{product_id} is not in your cart.",
        "cart_header": "Here’s what you have in your cart:",
        "cart_total": "Total: €{total:.2f}",
        "cart_next": "",
        "cart_partial_add_note": " (Requested {qty}, added {added} due to stock limits.)",
        "cart_partial_remove_note": " (Requested {qty}, removed {removed} because you had fewer units in the cart.)",
        "cart_next_after_action": "",
        "cart_next_after_add": "",

        # Generic / clarification
        "ok": "Okay.",
        "reply_number_id_name": "Reply with the number, the ID, or the name.",
        "reply_number_id": "Reply with the option number (1, 2…) or the product ID.",
        "multiple_matches_which_view": "I found multiple matches. Which one do you want to view?",
        "multiple_matches_which_add": "I found multiple matches. Which one did you mean?",
        "multiple_matches_which_remove": "I found multiple matches. Which one do you want to remove?",
        "multiple_matches_which_adjust": "I found multiple matches. Which one do you want to adjust?",
        "ask_which_product": "Which product do you mean? Tell me the ID or the name.",
        "invalid_option_number": "That number is invalid.",
        "id_not_in_options": "That ID is not among the options.",

        # Clarify / product choice
        "clarify_pick_one": "Which one do you want? Reply with the number, ID, or name.",
        "clarify_id_not_in_options": "That ID is not among the options.",
        "clarify_invalid_number": "That number is invalid.",
        "clarify_detail_next": 'You can say: "Add it to the cart" or "Back to catalog".',

        "clarify_added": (
            "Added ✅ {product_label} x{qty}\n"
            "Total: €{total:.2f}"
        ),
        "clarify_removed": (
            "Removed ✅ {product_label} x{qty}\n"
            "Total: €{total:.2f}"
        ),
        "clarify_not_in_cart": "That product is not in your cart.",
        "clarify_set_qty_failed": "I couldn't update the quantity.",
        "clarify_qty_updated": (
            "Quantity updated ✅ {product_label} x{qty}\n"
            "Total: €{total:.2f}"
        ),

        # (requested): Adjust qty / clarify pick
        "qty_set_ok": "Quantity updated ✅ [{product_id}] {brand} - {name} x{qty}\nTotal: €{total:.2f}",
        "need_product_id_or_name": "Which product do you mean? Tell me the ID or the name.",
        "pick_number_id_or_name": "Reply with the number, the ID, or the name.",
        "adjust_multiple_found": "I found multiple matches. Which one do you want to adjust?",
        "adjust_which_of_these": "Which of these products do you mean?",
        # (requested): Bulk clarification
        "bulk_reply_number_id": "Reply with the option number (1, 2…) or the product ID.",
        "bulk_multiple_found": "I found multiple matches. Which one did you mean?",

        # Checkout (chat copy, NO form)
        "checkout_open_form": "Perfect ✅ Opening the checkout form for your shipping details.",
        "checkout_cancel_back_cart": "Okay 👍 I cancelled the order. Back to your cart.",
        "checkout_review_header": "Perfect ✅ Here is your order summary:",
        "checkout_confirm_purchase": "Do you confirm the purchase? (yes/no)",
        "checkout_confirmed": (
            "Order confirmed ✅\n\n"
            "Thanks for your purchase 🙌\n"
            "Do you want to see the catalog, recommendations, or your cart?"
        ),

        # Adjust qty
        "qty_set_done": "Done ✅ Set {product_label} to {qty} unit(s).\n\nTotal: €{total:.2f}",
        "qty_update_failed": "I couldn't update the quantity.",
        "adjust_pick_product": "Which of these products do you mean?",
        "adjust_need_product": "Which product do you mean? Tell me the ID or the name.",
        "adjust_qty_failed": "I couldn't update the quantity.",

        # Catalog/product search
        "product_not_found_hint": "I couldn't find that product. Tell me the ID or a more specific name.",

        # Bulk
        "bulk_none": "I couldn’t find cart operations to apply.",
        "bulk_added": "✅ Added {added} of {product_label}{note}",
        "bulk_removed": "✅ Removed {removed} of {product_label}",
        "bulk_not_found": "❌ Product {product_id} was not found.",
        "bulk_no_stock": "❌ No stock available for {product_label}.",
        "bulk_not_in_cart": "❌ {product_label} is not in your cart.",
        "bulk_cannot_remove": "❌ I can't remove {qty} of {product_label} because you only have {current_qty}.",
        "bulk_total": "Current total: €{total:.2f}",
        "bulk_next": "",
        "bulk_partial_add_note": " (Requested {qty}, added {added} due to stock limits.)",
        "bulk_remove_failed": "❌ Could not remove {product_label}.",
        "bulk_multiple_found": "I found multiple matches. Which one did you mean?",
        "bulk_reply_number_id": "Reply with the option number (1, 2…) or the product ID.",

        # Checkout
        "checkout_confirm": "You're about to checkout. Do you want to continue? (yes/no)",
        "checkout_cancelled": "Checkout cancelled.",
        "checkout_ask_yesno": "Please reply with 'yes' or 'no'.",
        "checkout_form_reminder": "To continue, please complete the shipping form I opened ✅",
        "shipping_ask_name": "What’s your full name for shipping?",
        "shipping_ask_city": "What city should we ship to?",
        "shipping_invalid": "Please provide a valid value.",
        "shipping_remaining": "Please provide the remaining shipping information.",
        "order_confirmed": (
            "Order confirmed ✅\n"
            "- Name: {name}\n"
            "- City: {city}\n\n"
            "Thank you for your purchase!"
        ),

        #Checkout form validations (submit_checkout_form)
        "checkout_form_missing_fields_error": "Please fill in all fields.",
        "checkout_form_missing_fields_msg": (
            "Oops 😅 some fields are missing. Please review the form and submit again."
        ),
        "checkout_form_postal_numeric_error": "Postal code must be numeric.",
        "checkout_form_postal_numeric_msg": (
            "Postal code must be numeric. Please fix it in the form and resubmit."
        ),
        "checkout_form_phone_numeric_error": "Phone must be numeric.",
        "checkout_form_phone_numeric_msg": (
            "Phone must be numeric. Please fix it in the form and resubmit."
        ),
        "checkout_review_prompt": (
            "Perfect ✅ I’ve got your details.\n\n"
            "Shipping summary:\n"
            "- Name: {full_name}\n"
            "- Address: {address_line1}\n"
            "- City: {city}\n"
            "- ZIP: {postal_code}\n"
            "- Phone: {phone}\n\n"
            "Do you confirm the order? (yes/no)"
        ),
        "checkout_form_open_guard": "The shipping form is open 👇 Please fill it in and click “Save details and continue”.",

    },
    "es": {
        # Generic
        "fallback_ok": "Vale.",
        "follow_up": "",
        "product_not_found": "No encuentro el producto {product_id}.",
        "cart_empty": "Tu carrito está vacío.",
        "need_product_id_add": 'Dime el ID del producto (ej: "Añade 301").',
        "need_product_id_remove": 'Dime el ID del producto (ej: "Quita 302").',

        #Welcome / Ended (moved from ChatEngine)
        "welcome": (
            "¡Saludos! 👋\n\n"
            "Seré tu asistente durante tu navegación por nuestra tienda.\n"
            "Puedes pedirme ver el catálogo, añadir perfumes al carrito o pedir recomendaciones.\n\n"
            "¿En qué puedo ayudarte?"
        ),
        "ended": "Conversación finalizada. Gracias por visitarnos.",

        # Catalog / Product details / Recommend
        "catalog_header": "Perfumes disponibles:",
        "catalog_next": "",
        "detail_multiple_found": "He encontrado varias opciones. ¿Cuál quieres ver?",
        "detail_multiple_reply_hint": "Responde con el número, el ID o el nombre.",
        "product_id_invalid": "Por favor, indica un ID de producto válido.",
        "product_details_header": "Detalles del producto {product_label}:",
        "product_price": "- Precio: €{price:.2f}",
        "product_concentration": "- Concentración: {value}",
        "product_size": "- Tamaño: {value} ml",
        "product_family": "- Familia olfativa: {value}",
        "product_description": "- Descripción: {value}",
        "product_details_next": "",
        "recommend_need_clarification": "¿Qué estilo de perfume quieres (cítrico, amaderado, floral, oriental…)? ¿Y tu presupuesto?",
        "recommend_no_results_in_price": "No tenemos perfumes {family_label} en ese rango de precio.",
        "recommend_but_have_family": "Pero sí tenemos estos perfumes {family_label}:",
        "recommend_no_family": "No tenemos perfumes de la familia {family_label}.",
        "family_generic_label": "esa familia",
        "catalog_item": "- [{product_id}] {brand}{name} — €{price:.2f}",
        "recommend_header": "Perfumes recomendados:",
        "recommend_next": "",
        "recommend_clarify": (
            "¿Qué tipo de perfume buscas (cítrico, amaderado, floral, oriental…)? "
            "¿Tienes un presupuesto máximo? (ej: 'amaderado menos de 100€')"
        ),
        "recommend_no_results_in_range": "No tenemos perfumes {family_label} en ese rango de precio.",
        "recommend_no_family": "No tenemos perfumes de la familia {family_label}.",
        "recommend_but_have_these": "Pero sí tenemos estos perfumes {family_label}:",
        "recommend_clarification_prompt": (
            "¿Qué tipo de perfume buscas (cítrico, amaderado, floral, oriental…)? "
            "¿Tienes un presupuesto máximo? (ej: 'amaderado menos de 100€')"
        ),


        # Generic / clarification
        "ok": "Vale.",
        "reply_number_id_name": "Responde con el número, el ID o el nombre.",
        "reply_number_id": "Responde con el número (1, 2…) o con el ID.",
        "multiple_matches_which_view": "He encontrado varias opciones. ¿Cuál quieres ver?",
        "multiple_matches_which_add": "He encontrado varias opciones. ¿A cuál te refieres?",
        "multiple_matches_which_remove": "He encontrado varias opciones. ¿Cuál quieres quitar?",
        "multiple_matches_which_adjust": "He encontrado varias opciones. ¿Cuál quieres ajustar?",
        "ask_which_product": "¿De qué producto hablamos? Dime el ID o el nombre.",
        "invalid_option_number": "Ese número no es válido.",
        "id_not_in_options": "Ese ID no está entre las opciones.",

        # Clarify / product choice
        "clarify_pick_one": "¿Cuál quieres? Responde con el número, el ID o el nombre.",
        "clarify_id_not_in_options": "Ese ID no está entre las opciones.",
        "clarify_invalid_number": "Ese número no es válido.",
        "clarify_detail_next": 'Puedes decir: "Añádelo al carrito" o "Volver al catálogo".',

        "clarify_added": (
            "Añadido ✅ {product_label} x{qty}\n"
            "Total: €{total:.2f}"
        ),
        "clarify_removed": (
            "Quitado ✅ {product_label} x{qty}\n"
            "Total: €{total:.2f}"
        ),
        "clarify_not_in_cart": "Ese producto no está en tu carrito.",
        "clarify_set_qty_failed": "No he podido actualizar la cantidad.",
        "clarify_qty_updated": (
            "Cantidad actualizada ✅ {product_label} x{qty}\n"
            "Total: €{total:.2f}"
        ),

        # (requested): Ajustar cantidad / elegir opción
        "qty_set_ok": "Cantidad actualizada ✅ [{product_id}] {brand} - {name} x{qty}\nTotal: €{total:.2f}",
        "need_product_id_or_name": "¿De qué producto hablamos? Dime el ID o el nombre.",
        "pick_number_id_or_name": "Responde con el número, el ID o el nombre.",
        "adjust_multiple_found": "He encontrado varias opciones. ¿Cuál quieres ajustar?",
        "adjust_which_of_these": "¿A cuál de estos productos te refieres?",
        # NEW (requested): Bulk clarification
        "bulk_reply_number_id": "Responde con el número (1, 2…) o con el ID.",
        "bulk_multiple_found": "He encontrado varias opciones. ¿A cuál te refieres?",

        # Checkout (chat copy, NO form)
        "checkout_open_form": "Perfecto ✅ Abro el formulario para tus datos de envío.",
        "checkout_cancel_back_cart": "Vale 👍 He cancelado el pedido. Vuelves al carrito.",
        "checkout_review_header": "Perfecto ✅ Aquí tienes el resumen del pedido:",
        "checkout_form_reminder": "Para continuar, completa el formulario de envío que tengo abierto ✅",
        "checkout_confirm_purchase": "¿Confirmas la compra? (sí/no)",
        "checkout_confirmed": (
            "¡Pedido confirmado! ✅\n\n"
            "Gracias por tu compra 🙌\n"
            "¿Quieres ver el catálogo, recomendaciones o tu carrito?"
        ),
        "checkout_form_open_guard_es": "Tengo el formulario de envío abierto 👇 Rellénalo y pulsa “Guardar datos y continuar”.",

        # Adjust qty
        "qty_set_done": "Perfecto ✅ Dejé {product_label} en {qty} unidad(es).\n\nTotal: €{total:.2f}",
        "qty_update_failed": "No he podido actualizar la cantidad.",
        "adjust_pick_product": "¿A cuál de estos productos te refieres?",
        "adjust_need_product": "¿De qué producto hablamos? Dime el ID o el nombre.",
        "adjust_qty_failed": "No he podido actualizar la cantidad.",

        # Catalog/product search
        "product_not_found_hint": "No encuentro ese producto. Dime el ID o un nombre más exacto.",

        # Cart actions
        "add_ok": "¡Hecho! ✅ Añadí {added} unidad(es) de {product_label} al carrito{note}.",
        "add_no_stock": "Lo siento — ahora mismo no hay stock de {product_label}.",
        "remove_ok": "Listo ✅ Quité {removed} unidad(es) de {product_label} del carrito{note}.",
        "remove_not_in_cart": "El producto {product_id} no está en tu carrito.",
        "cart_header": "Esto es lo que llevas en el carrito:",
        "cart_total": "Total: €{total:.2f}",
        "cart_next": "",
        "cart_partial_add_note": " (Pediste {qty}, añadí {added} por límite de stock.)",
        "cart_partial_remove_note": " (Pediste quitar {qty}, pero solo pude quitar {removed} porque tenías menos.)",
        "cart_next_after_action": "",
        "cart_next_after_add": "",

        # Bulk
        "bulk_none": "No he encontrado operaciones de carrito para aplicar.",
        "bulk_added": "✅ Añadí {added} de {product_label}{note}",
        "bulk_removed": "✅ Quité {removed} de {product_label}",
        "bulk_not_found": "❌ El producto {product_id} no existe.",
        "bulk_no_stock": "❌ No hay stock disponible para {product_label}.",
        "bulk_not_in_cart": "❌ {product_label} no está en tu carrito.",
        "bulk_cannot_remove": "❌ No puedo quitar {qty} de {product_label} porque solo tienes {current_qty}.",
        "bulk_total": "Total actual: €{total:.2f}",
        "bulk_next": "",
        "bulk_partial_add_note": " (Pediste {qty}, añadí {added} por límite de stock.)",
        "bulk_remove_failed": "❌ No he podido quitar {product_label}.",
        "bulk_multiple_found": "He encontrado varias opciones. ¿A cuál te refieres?",
        "bulk_reply_number_id": "Responde con el número (1, 2…) o con el ID.",

        # Checkout
        "checkout_confirm": "Vas a finalizar la compra. ¿Quieres continuar? (sí/no)",
        "checkout_cancelled": "Compra cancelada.",
        "checkout_ask_yesno": "Por favor, responde con 'sí' o 'no'.",
        "shipping_ask_name": "¿Cuál es tu nombre completo para el envío?",
        "shipping_ask_city": "¿A qué ciudad hacemos el envío?",
        "shipping_invalid": "Por favor, dame un valor válido.",
        "shipping_remaining": "Por favor, proporciona la información de envío que falta.",
        "order_confirmed": (
            "Pedido confirmado ✅\n"
            "- Nombre: {name}\n"
            "- Ciudad: {city}\n\n"
            "¡Gracias por tu compra!"
        ),

        # Checkout form validations (submit_checkout_form)
        "checkout_form_missing_fields_error": "Rellena todos los campos.",
        "checkout_form_missing_fields_msg": (
            "Ups 😅 faltan campos. Revisa el formulario y vuelve a enviarlo."
        ),
        "checkout_form_postal_numeric_error": "El código postal debe ser numérico.",
        "checkout_form_postal_numeric_msg": (
            "El código postal debe ser numérico. Corrígelo en el formulario y reenvíalo."
        ),
        "checkout_form_phone_numeric_error": "El teléfono debe ser numérico.",
        "checkout_form_phone_numeric_msg": (
            "El teléfono debe ser numérico. Corrígelo en el formulario y reenvíalo."
        ),
        "checkout_review_prompt": (
            "Perfecto ✅ Ya tengo tus datos.\n\n"
            "Resumen del envío:\n"
            "- Nombre: {full_name}\n"
            "- Dirección: {address_line1}\n"
            "- Ciudad: {city}\n"
            "- CP: {postal_code}\n"
            "- Teléfono: {phone}\n\n"
            "¿Confirmas el pedido? (sí/no)"
        ),
    },
}


def _lang(state: ConversationState) -> str:

    """
    Resolve the active language for the current conversation state.

    Defaults to English if no preference is set.
    """

    lang = (state.preferred_language or "en").lower()
    return "es" if lang == "es" else "en"


def t(state: ConversationState, key: str, **kwargs: Any) -> str:
    """
    Return a localized message template formatted with the given placeholders.

    Falls back to English if the key is missing in the requested language.
    If formatting fails, returns the unformatted template.
    """
    lang = _lang(state)
    template = _COPY.get(lang, {}).get(key) or _COPY["en"].get(key)
    if template is None:
        return key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
