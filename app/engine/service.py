from __future__ import annotations

import logging
from typing import Literal

from app.engine.response import finalize_assistant_message
from app.engine.state import Mode
from app.graph.builder import build_graph

from .memory import InMemorySessionStore
from .state import ConversationState

logger = logging.getLogger(__name__)

WELCOME_ES = (
    "¡Saludos! 👋\n\n"
    "Seré tu asistente durante tu navegación por nuestra tienda.\n"
    "Puedes pedirme ver el catálogo, añadir perfumes al carrito o pedir recomendaciones.\n\n"
    "¿En qué puedo ayudarte?"
)

WELCOME_EN = (
    "Hi! 👋\n\n"
    "I’ll be your assistant while you browse our store.\n"
    "You can ask me to show the catalog, add perfumes to the cart, or get recommendations.\n\n"
    "How can I help you?"
)

ENDED_ES = "Conversación finalizada. Gracias por visitarnos."
ENDED_EN = "Conversation ended. Thank you for visiting."


def _detect_language_switch_or_greeting(text: str) -> Literal["es", "en"] | None:
    t = (text or "").lower().strip()

    if any(k in t for k in ["in english", "english please", "speak english"]):
        return "en"
    if any(k in t for k in ["en español", "en espanol", "habla español", "habla espanol"]):
        return "es"

    if t in {"hi", "hello", "hey"}:
        return "en"
    if t in {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}:
        return "es"

    return None


class ChatEngine:
    def __init__(self) -> None:
        self._store = InMemorySessionStore()
        self._graph = build_graph()

    def start_session(
        self,
        session_id: str,
        language: Literal["es", "en"] | None = None,
    ) -> ConversationState:
        state = self._store.get(session_id)
        if state is not None:
            return state

        state = ConversationState(session_id=session_id)
        lang = language or "es"
        state.preferred_language = lang
        state.assistant_message = WELCOME_ES if lang == "es" else WELCOME_EN
        self._store.set(state)
        return state

    def submit_checkout_form(
        self,
        session_id: str,
        full_name: str,
        address_line1: str,
        city: str,
        postal_code: str,
        phone: str,
    ) -> ConversationState:
        state = self._store.get(session_id)
        if state is None:
            state = self.start_session(session_id=session_id)

        # ✅ HARD STOP si ya terminó
        if state.should_end or state.mode == Mode.END:
            lang = state.preferred_language or "es"
            state.assistant_message = ENDED_ES if lang == "es" else ENDED_EN
            state.ui_show_checkout_form = False
            state.ui_form_error = None
            self._store.set(state)
            return state

        lang = state.preferred_language or "es"
        state.ui_form_error = None

        full_name = (full_name or "").strip()
        address_line1 = (address_line1 or "").strip()
        city = (city or "").strip()
        postal_code = (postal_code or "").strip()
        phone = (phone or "").strip()

        if not full_name or not address_line1 or not city or not postal_code or not phone:
            state.ui_form_error = "Rellena todos los campos." if lang == "es" else "Please fill in all fields."
            state.ui_show_checkout_form = True
            state.assistant_message = (
                "Ups 😅 faltan campos. Revisa el formulario y vuelve a enviarlo."
                if lang == "es"
                else "Oops 😅 some fields are missing. Please review the form and submit again."
            )
            self._store.set(state)
            return state

        if not postal_code.replace(" ", "").isdigit():
            state.ui_form_error = (
                "El código postal debe ser numérico."
                if lang == "es"
                else "Postal code must be numeric."
            )
            state.ui_show_checkout_form = True
            state.assistant_message = (
                "El código postal debe ser numérico. Corrígelo en el formulario y reenvíalo."
                if lang == "es"
                else "Postal code must be numeric. Please fix it in the form and resubmit."
            )
            self._store.set(state)
            return state

        # ✅ NEW: validar teléfono numérico también
        if not phone.replace(" ", "").isdigit():
            state.ui_form_error = (
                "El teléfono debe ser numérico."
                if lang == "es"
                else "Phone must be numeric."
            )
            state.ui_show_checkout_form = True
            state.assistant_message = (
                "El teléfono debe ser numérico. Corrígelo en el formulario y reenvíalo."
                if lang == "es"
                else "Phone must be numeric. Please fix it in the form and resubmit."
            )
            self._store.set(state)
            return state

        state.shipping.full_name = full_name
        state.shipping.address_line1 = address_line1
        state.shipping.city = city
        state.shipping.postal_code = postal_code
        state.shipping.phone = phone

        state.ui_show_checkout_form = False
        state.mode = Mode.CHECKOUT_REVIEW

        if lang == "es":
            state.assistant_message = (
                "Perfecto ✅ Ya tengo tus datos.\n\n"
                "Resumen del envío:\n"
                f"- Nombre: {state.shipping.full_name}\n"
                f"- Dirección: {state.shipping.address_line1}\n"
                f"- Ciudad: {state.shipping.city}\n"
                f"- CP: {state.shipping.postal_code}\n"
                f"- Teléfono: {state.shipping.phone}\n\n"
                "¿Confirmas el pedido? (sí/no)"
            )
        else:
            state.assistant_message = (
                "Perfect ✅ I’ve got your details.\n\n"
                "Shipping summary:\n"
                f"- Name: {state.shipping.full_name}\n"
                f"- Address: {state.shipping.address_line1}\n"
                f"- City: {state.shipping.city}\n"
                f"- ZIP: {state.shipping.postal_code}\n"
                f"- Phone: {state.shipping.phone}\n\n"
                "Do you confirm the order? (yes/no)"
            )

        finalize_assistant_message(state)
        self._store.set(state)
        return state

    def process_turn(self, session_id: str, user_message: str) -> ConversationState:
        state = self._store.get(session_id)
        if state is None:
            state = self.start_session(session_id=session_id)
            if not (user_message or "").strip():
                return state

        # ✅ HARD STOP: no aceptar más mensajes tras END
        if state.should_end or state.mode == Mode.END:
            lang = state.preferred_language or "es"
            state.assistant_message = ENDED_ES if lang == "es" else ENDED_EN
            state.ui_show_checkout_form = False
            state.ui_form_error = None
            self._store.set(state)
            return state

        state.user_message = user_message

        switch_lang = _detect_language_switch_or_greeting(user_message)
        if switch_lang in ("es", "en"):
            state.preferred_language = switch_lang
            state.assistant_message = WELCOME_ES if switch_lang == "es" else WELCOME_EN
            self._store.set(state)
            return state

        result = self._graph.invoke(state)

        if isinstance(result, dict):
            new_state = ConversationState.model_validate(result)
        else:
            new_state = result

        finalize_assistant_message(new_state)
        self._store.set(new_state)
        return new_state

    def reset(self, session_id: str) -> None:
        self._store.reset(session_id)
