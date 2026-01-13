from __future__ import annotations

import re
from typing import Callable

from app.engine.state import ConversationState, Mode
from app.utils import (
    parse_cart_commands,
    parse_adjustment,
    parse_cart_commands_by_name,
    parse_recommend_slots,
    parse_qty_only
)

Rule = Callable[[ConversationState], bool]

# ✅ NUEVO: checkout intent fuerte (ES/EN)
_CHECKOUT_RE = re.compile(
    r"\b("
    r"checkout|pay|payment|"
    r"pago|pagar|hacer el pago|"
    r"finalizar(?:\s+la)?\s+compra|tramitar(?:\s+pedido)?"
    r")\b",
    re.IGNORECASE,
)

# -------------------------
# Helpers
# -------------------------
def _msg_l(state: ConversationState) -> str:
    return (state.user_message or "").strip().lower()


def _explicit_language_switch(text: str) -> bool:
    t = (text or "").lower()
    return any(
        k in t
        for k in [
            "en español",
            "en espanol",
            "habla español",
            "habla espanol",
            "in english",
            "speak english",
            "english please",
        ]
    )


def _detect_language_heuristic(text: str) -> str | None:
    t = (text or "").lower()

    if any(k in t for k in ["en español", "en espanol", "habla español", "habla espanol"]):
        return "es"
    if any(k in t for k in ["in english", "speak english", "english please"]):
        return "en"

    if any(
        k in t
        for k in [
            "show", "tell me", "details", "add", "remove", "delete",
            "cart", "pay", "recommend", "under", "cheaper",
            "please", "in english","make it", "set it", "change it", "only", "just", "instead","yes","help"
        ]
    ):
        return "en"

    if any(ch in t for ch in ["¿", "¡", "ñ", "á", "é", "í", "ó", "ú"]):
        return "es"

    if any(
        k in t
        for k in [
            "añade", "anade", "añadir",
            "quita", "quitar", "carrito",
            "muestrame", "muéstrame",
            "ensename", "enseñame", "enséñame",
            "recomendar", "recomendarme", "recomiendame", "recomiéndame",
            "precio", "catalogo", "catálogo",
            "menos de", "euros", "hombre", "mujer",
            "quiero", "puedes", "me puedes",
            "amaderado", "amaderados", "maderoso", "maderosos",
            "cítrico", "citrico", "cítricos", "citricos",
            "floral", "florales",
            "oriental", "orientales", "ámbar", "ambar",
            "acuático", "acuatico", "acuáticos", "acuaticos", "marino", "marinos",
            "aromático", "aromatico", "aromáticos", "aromaticos",
            "dulce", "dulces", "gourmand",
            "afrutado", "afrutados", "frutal", "frutales",
            "cuero","mejor", "solo", "que sea", "que sean", "cámbialo", "cambialo", "en vez de",
        ]
    ):
        return "es"

    return None


def _ask_recommend_clarification(state: ConversationState, lang: str) -> None:
    state.assistant_message = (
        "¿Qué tipo de perfume buscas (cítrico, amaderado, floral, oriental…)? "
        "¿Tienes un presupuesto máximo? (ej: 'amaderado menos de 100€')"
        if lang == "es"
        else "What kind of perfume do you want (woody, citrus, floral, oriental…)? "
             "Do you have a max budget? (e.g. 'woody under 100€')"
    )
    state.next_node = "echo"
    state.pending_recommend_clarification = True


def _merge_recommend_slots(state: ConversationState, slots) -> None:
    if slots.families:
        state.recommended_family = slots.families
    if slots.audience is not None:
        state.recommended_audience = slots.audience
    if slots.min_price is not None:
        state.recommended_min_price = slots.min_price
    if slots.max_price is not None:
        state.recommended_max_price = slots.max_price


def _recommend_is_still_empty(state: ConversationState) -> bool:
    return (
        not (getattr(state, "recommended_family", None) or [])
        and getattr(state, "recommended_audience", None) is None
        and getattr(state, "recommended_min_price", None) is None
        and getattr(state, "recommended_max_price", None) is None
    )


# -------------------------
# Rules
# -------------------------
def rule_exit(state: ConversationState) -> bool:
    msg_l = _msg_l(state)

    EXIT_KEYWORDS = {
        "salir", "terminar", "finalizar", "cerrar", "fin",
        "exit", "end", "quit", "bye", "adiós", "adios",
    }

    if any(re.search(rf"\b{k}\b", msg_l) for k in EXIT_KEYWORDS):
        state.mode = Mode.END
        state.should_end = True
        state.assistant_message = (
            "Conversación finalizada. Gracias por visitarnos."
            if (state.preferred_language or "en") == "es"
            else "Conversation ended. Thank you for visiting."
        )
        return True

    return False


def rule_pending_bulk(state: ConversationState) -> bool:
    if getattr(state, "pending_bulk_op", None) and state.candidate_products:
        if re.search(r"\b(\d{1,3})\b", state.user_message or ""):
            state.next_node = "bulk_cart_update"
            return True
        state.pending_bulk_op = None
        state.pending_bulk_qty = None
        state.candidate_products = []
    return False


def rule_pending_product(state: ConversationState) -> bool:
    if state.pending_product_op and state.candidate_products:
        if re.search(r"\b(\d{1,3})\b", state.user_message or ""):
            state.next_node = (
                "adjust_cart_qty"
                if state.pending_product_op == "set_qty"
                else "resolve_product_choice"
            )
            return True
        state.next_node = "resolve_product_choice"
        return True
    return False


def rule_language_detection(state: ConversationState) -> bool:
    detected = _detect_language_heuristic(state.user_message)

    if state.preferred_language is None:
        state.preferred_language = detected or "es"
    elif _explicit_language_switch(state.user_message):
        state.preferred_language = detected or state.preferred_language
    elif detected and detected != state.preferred_language:
        state.preferred_language = detected

    return False


def rule_mode_guardrails(state: ConversationState) -> bool:
    if state.mode == Mode.CHECKOUT_CONFIRM:
        state.next_node = "handle_checkout_confirmation"
        return True

    if state.mode == Mode.CHECKOUT_REVIEW:
        state.next_node = "handle_checkout_review"
        return True

    if state.mode == Mode.COLLECT_SHIPPING:
        state.next_node = "collect_shipping"
        return True

    return False


def rule_checkout(state: ConversationState) -> bool:
    msg = (state.user_message or "").strip().lower()
    if not msg:
        return False
    if _CHECKOUT_RE.search(msg):
        state.next_node = "checkout_confirm"
        return True
    return False


def apply_recommend_heuristic(state: ConversationState) -> bool:
    msg_l = _msg_l(state)

    pending = bool(getattr(state, "pending_recommend_clarification", False))
    is_trigger = bool(re.search(r"\b(recom|recommend)\w*\b", msg_l))

    if not pending and not is_trigger:
        return False

    detected = _detect_language_heuristic(state.user_message)
    if detected:
        state.preferred_language = detected

    lang = state.preferred_language or "es"

    slots = parse_recommend_slots(state.user_message, lang=lang)
    _merge_recommend_slots(state, slots)

    if _recommend_is_still_empty(state):
        _ask_recommend_clarification(state, lang)
        return True

    state.pending_recommend_clarification = False
    state.next_node = "recommend_product"
    return True


def rule_show_catalog(state: ConversationState) -> bool:
    msg_l = _msg_l(state)

    if any(
        k in msg_l
        for k in [
            # ES
            "catálogo", "catalogo",
            "ver el catálogo", "ver el catalogo",
            "el catálogo", "el catalogo",
            "que perfumes tienes",
            "que tienes para mostrarme",
            "que vendes",
            "que productos tienes",

            # EN
            "catalog", "catalogue",
            "the catalog",
            "show the catalog",
            "show me the catalog",
            "what perfumes do you have",
            "what do you have",
            "what do you sell",
            "list perfumes",
            "show me what you have",
        ]
    ):
        state.next_node = "show_catalog"
        return True

    return False


def rule_adjust_qty(state: ConversationState) -> bool:
    target_qty, _ = parse_adjustment(state.user_message)
    if target_qty is not None:
        state.next_node = "adjust_cart_qty"
        return True
    return False


def rule_bulk_cart_ids(state: ConversationState) -> bool:
    bulk_actions = parse_cart_commands(state.user_message)
    if len(bulk_actions) >= 2:
        state.pending_actions = bulk_actions
        state.next_node = "bulk_cart_update"
        return True
    return False


def rule_bulk_cart_names(state: ConversationState) -> bool:
    actions_with_ids, name_actions = parse_cart_commands_by_name(state.user_message)
    if (len(actions_with_ids) + len(name_actions) >= 2) and name_actions:
        state.pending_actions = actions_with_ids
        state.pending_name_actions = [f"{op.value}|{qty}|{hint}" for op, qty, hint in name_actions]
        state.next_node = "bulk_cart_update"
        return True
    return False


def rule_single_cart_command(state: ConversationState) -> bool:
    msg = state.user_message or ""
    msg_l = _msg_l(state)

    # 1) Si el texto trae un ID 3 dígitos, úsalo directamente
    #    Ej: "quita 1 del 302"
    actions = parse_cart_commands(msg)
    if len(actions) == 1:
        a = actions[0]
        state.selected_product_id = a.product_id
        state.pending_qty = a.qty
        state.next_node = "add_to_cart" if a.op.value == "add" else "remove_from_cart"
        return True

    # 2) Si NO trae ID pero sí trae "quitame 1" y ya hay selected_product_id
    #    Ej: usuario vio un producto antes
    if state.selected_product_id is not None:
        m = re.search(r"\b(\d{1,2})\b", msg_l)
        if m and any(k in msg_l for k in ["quitame", "quítame", "quita", "remove", "delete", "saca", "borra"]):
            state.pending_qty = int(m.group(1))
            state.next_node = "remove_from_cart"
            return True

    return False


def rule_view_cart(state: ConversationState) -> bool:
    msg_l = _msg_l(state)
    if any(
        k in msg_l
        for k in [
            "carrito", "ver carrito", "muéstrame el carrito", "muestrame el carrito",
            "cart", "show cart", "show me the cart", "view cart", "Que llevo en el carrito"
        ]
    ):
        state.next_node = "view_cart"
        return True
    return False


def rule_product_detail_by_id(state: ConversationState) -> bool:
    msg_l = _msg_l(state)
    if re.search(r"\b\d{3}\b", state.user_message or "") and any(
        k in msg_l for k in ["muestrame", "muéstrame", "enseñame", "enséñame", "show me"]
    ):
        state.next_node = "show_product_detail"
        return True
    return False


def rule_product_detail_by_name(state: ConversationState) -> bool:
    msg_l = _msg_l(state)
    if any(k in msg_l for k in ["muestrame", "muéstrame", "enseñame", "enséñame", "show me"]):
        if not re.search(r"\b\d{3}\b", state.user_message or ""):
            state.next_node = "show_product_detail"
            return True
    return False


_HELP_RE = re.compile(
    r"\b("
    r"(que|qué)\s+(puedes|pod(es|és))\s+(hacer|ayudar)|"
    r"(en\s+que|en\s+qué)\s+me\s+puedes\s+ayudar|"
    r"ayuda|help|"
    r"what\s+can\s+you\s+do|"
    r"how\s+can\s+you\s+help|"
    r"what\s+do\s+you\s+do"
    r")\b",
    re.IGNORECASE,
)

def rule_help(state: ConversationState) -> bool:
    msg = (state.user_message or "").strip()
    if not msg:
        return False

    if not _HELP_RE.search(msg):
        return False

    lang = state.preferred_language or "es"

    state.assistant_message = (
        "Puedo ayudarte con esto:\n"
        "- Ver el catálogo (ej: “muéstrame el catálogo”)\n"
        "- Ver detalles de un perfume por ID o nombre (ej: “enséñame el 318”, “muéstrame Libre”)\n"
        "- Añadir/quitar perfumes al carrito (ej: “añade 302”, “quita 1 del 302”, “añádelo al carrito”)\n"
        "- Ver el carrito y el total (ej: “ver carrito”)\n"
        "- Recomendaciones por familia/ precio/ público (ej: “amaderado menos de 100€”, “floral para mujer”)\n"
        "- Finalizar compra (ej: “quiero pagar / finalizar compra”)\n"
        "\n¿Quieres que te enseñe el catálogo o te recomiendo algo?"
        if lang == "es"
        else
        "I can help with:\n"
        "- Show the catalog (e.g., “show me the catalog”)\n"
        "- Show product details by ID or name (e.g., “show 318”, “show Libre”)\n"
        "- Add/remove items from your cart (e.g., “add 302”, “remove 1 of 302”, “add it to cart”)\n"
        "- View your cart and total (e.g., “view cart”)\n"
        "- Recommendations by family/price/audience (e.g., “woody under 100€”, “floral for women”)\n"
        "- Checkout (e.g., “checkout / pay”)\n"
        "\nDo you want to see the catalog or get a recommendation?"
    )

    state.next_node = "echo"
    return True

def rule_out_of_scope(state: ConversationState) -> bool:
    lang = (state.preferred_language or "es")
    state.assistant_message = (
        "No puedo ayudarte con eso. Puedo enseñarte el catálogo, recomendar perfumes o gestionar tu carrito."
        if lang == "es"
        else "I can’t help with that. I can show the catalog, recommend perfumes, or manage your cart."
    )
    state.next_node = "echo"
    return True

def rule_cart_commands_any(state: ConversationState) -> bool:
    actions = parse_cart_commands(state.user_message)

    if not actions:
        return False

    if len(actions) == 1:
        a = actions[0]
        state.selected_product_id = a.product_id
        state.pending_qty = a.qty
        state.next_node = "add_to_cart" if a.op.value == "add" else "remove_from_cart"
        return True

    # 2 o más => bulk
    state.pending_actions = actions
    state.next_node = "bulk_cart_update"
    return True

def rule_implicit_cart_op(state: ConversationState) -> bool:
    msg_l = _msg_l(state)
    if not msg_l:
        return False

    # 1) Detect intent "add" ES/EN
    add_verbs = [
        # ES
        "añade", "anade", "añadir", "agrega", "mete", "pon",
        # EN
        "add", "put", "take",
    ]
    wants_add = any(v in msg_l for v in add_verbs)
    if not wants_add:
        return False

    # 2) Extract qty from free-text (works for "add 2", "añade 2", "x2", "2 unidades")
    qty = parse_qty_only(state.user_message)
    if qty is None:
        # If user says just "add" / "añade" without a number, default to 1
        qty = 1

    # 3) Resolve product context
    product_id: int | None = None

    if state.selected_product_id:
        product_id = state.selected_product_id
    elif len(state.last_cart_product_ids) == 1:
        product_id = state.last_cart_product_ids[0]
        # rehydrate "active product" context so next turns behave naturally
        state.selected_product_id = product_id
    else:
        return False  # no context to apply the implicit add

    # 4) Route to add_to_cart using existing node logic
    state.pending_qty = qty
    state.next_node = "add_to_cart"
    return True


# Orden importa
RULES: list[Rule] = [
    rule_exit,
    rule_language_detection,
    rule_pending_bulk,
    rule_pending_product,
    rule_mode_guardrails,
    rule_checkout,
    apply_recommend_heuristic,
    rule_show_catalog,
    rule_help,
    rule_adjust_qty,
    rule_bulk_cart_ids,
    rule_bulk_cart_names,
    rule_single_cart_command,
    rule_implicit_cart_op,
    rule_view_cart,
    rule_product_detail_by_id,
    rule_product_detail_by_name,
    rule_out_of_scope,
    rule_cart_commands_any
]
