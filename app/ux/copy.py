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

        # Catalog / Product details / Recommend
        "catalog_header": "Available perfumes:",
        "catalog_next": "",

        "product_id_invalid": "Please specify a valid product ID.",
        "product_details_header": "Product details for {product_label}:",
        "product_price": "- Price: €{price:.2f}",
        "product_concentration": "- Concentration: {value}",
        "product_size": "- Size: {value} ml",
        "product_family": "- Olfactory family: {value}",
        "product_description": "- Description: {value}",
        "product_details_next": "",

        "recommend_header": "Recommended perfumes:",
        "recommend_next": "",

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

        # Checkout
        "checkout_confirm": "You're about to checkout. Do you want to continue? (yes/no)",
        "checkout_cancelled": "Checkout cancelled.",
        "checkout_ask_yesno": "Please reply with 'yes' or 'no'.",
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
    },
    "es": {
        # Generic
        "fallback_ok": "Vale.",
        "follow_up": "",
        "product_not_found": "No encuentro el producto {product_id}.",
        "cart_empty": "Tu carrito está vacío.",
        "need_product_id_add": 'Dime el ID del producto (ej: "Añade 301").',
        "need_product_id_remove": 'Dime el ID del producto (ej: "Quita 302").',

        # Catalog / Product details / Recommend
        "catalog_header": "Perfumes disponibles:",
        "catalog_next": "",

        "product_id_invalid": "Por favor, indica un ID de producto válido.",
        "product_details_header": "Detalles del producto {product_label}:",
        "product_price": "- Precio: €{price:.2f}",
        "product_concentration": "- Concentración: {value}",
        "product_size": "- Tamaño: {value} ml",
        "product_family": "- Familia olfativa: {value}",
        "product_description": "- Descripción: {value}",
        "product_details_next": "",

        "recommend_header": "Perfumes recomendados:",
        "recommend_next": "",

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
    },
}


def _lang(state: ConversationState) -> str:
    lang = (state.preferred_language or "en").lower()
    return "es" if lang == "es" else "en"


def t(state: ConversationState, key: str, **kwargs: Any) -> str:
    """
    Translation / copy helper.
    """
    lang = _lang(state)
    template = _COPY.get(lang, {}).get(key) or _COPY["en"].get(key)
    if template is None:
        return key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
