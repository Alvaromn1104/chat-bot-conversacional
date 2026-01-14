from __future__ import annotations

from typing import Literal

from app.engine.response import finalize_assistant_message
from app.engine.state import Mode
from app.graph.builder import build_graph
from app.ux import t

from .memory import InMemorySessionStore
from .state import ConversationState


def _detect_language_switch_or_greeting(text: str) -> Literal["es", "en"] | None:
    """
    Lightweight heuristic to detect language preference changes or greetings.

    This avoids an LLM roundtrip for trivial intents (e.g., "hello", "en español"),
    keeping response latency low and behavior deterministic.
    """
    t0 = (text or "").lower().strip()

    if any(k in t0 for k in ["in english", "english please", "speak english"]):
        return "en"
    if any(k in t0 for k in ["en español", "en espanol", "habla español", "habla espanol"]):
        return "es"

    if t0 in {"hi", "hello", "hey"}:
        return "en"
    if t0 in {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}:
        return "es"

    return None


class ChatEngine:
    """
    Orchestrates session state and routes each user turn through the LangGraph.

    The engine keeps session state in an in-memory store (suitable for local/dev)
    and reuses a single compiled graph instance across requests.
    """

    def __init__(self) -> None:
        self._store = InMemorySessionStore()
        self._graph = build_graph()

    def start_session(
        self,
        session_id: str,
        language: Literal["es", "en"] | None = None,
    ) -> ConversationState:
        """
        Initialize a new session if it doesn't exist, returning the current state.
        """
        state = self._store.get(session_id)
        if state is not None:
            return state

        state = ConversationState(session_id=session_id)
        state.preferred_language = language or "es"
        state.assistant_message = t(state, "welcome")
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
        """
        Validate and persist checkout form fields, then move the session to review.
        """
        state = self._store.get(session_id)
        if state is None:
            state = self.start_session(session_id=session_id)

        # Do not accept checkout data once the conversation has ended.
        if state.should_end or state.mode == Mode.END:
            state.assistant_message = t(state, "ended")
            state.ui_show_checkout_form = False
            state.ui_form_error = None
            self._store.set(state)
            return state

        state.ui_form_error = None

        full_name = (full_name or "").strip()
        address_line1 = (address_line1 or "").strip()
        city = (city or "").strip()
        postal_code = (postal_code or "").strip()
        phone = (phone or "").strip()

        # Basic server-side validation for required fields and numeric constraints.
        if not full_name or not address_line1 or not city or not postal_code or not phone:
            state.ui_form_error = t(state, "checkout_form_missing_fields_error")
            state.ui_show_checkout_form = True
            state.assistant_message = t(state, "checkout_form_missing_fields_msg")
            self._store.set(state)
            return state

        if not postal_code.replace(" ", "").isdigit():
            state.ui_form_error = t(state, "checkout_form_postal_numeric_error")
            state.ui_show_checkout_form = True
            state.assistant_message = t(state, "checkout_form_postal_numeric_msg")
            self._store.set(state)
            return state

        if not phone.replace(" ", "").isdigit():
            state.ui_form_error = t(state, "checkout_form_phone_numeric_error")
            state.ui_show_checkout_form = True
            state.assistant_message = t(state, "checkout_form_phone_numeric_msg")
            self._store.set(state)
            return state

        state.shipping.full_name = full_name
        state.shipping.address_line1 = address_line1
        state.shipping.city = city
        state.shipping.postal_code = postal_code
        state.shipping.phone = phone

        state.ui_show_checkout_form = False
        state.mode = Mode.CHECKOUT_REVIEW

        state.assistant_message = t(
            state,
            "checkout_review_prompt",
            full_name=state.shipping.full_name,
            address_line1=state.shipping.address_line1,
            city=state.shipping.city,
            postal_code=state.shipping.postal_code,
            phone=state.shipping.phone,
        )

        finalize_assistant_message(state)
        self._store.set(state)
        return state

    def process_turn(self, session_id: str, user_message: str) -> ConversationState:
        """
        Process a single user turn through the conversation graph.
        """
        state = self._store.get(session_id)
        if state is None:
            state = self.start_session(session_id=session_id)
            if not (user_message or "").strip():
                return state

        # Do not process further messages after reaching an end state.
        if state.should_end or state.mode == Mode.END:
            state.assistant_message = t(state, "ended")
            state.ui_show_checkout_form = False
            state.ui_form_error = None
            self._store.set(state)
            return state

        state.user_message = user_message

        switch_lang = _detect_language_switch_or_greeting(user_message)
        if switch_lang in ("es", "en"):
            state.preferred_language = switch_lang
            state.assistant_message = t(state, "welcome")
            self._store.set(state)
            return state

        # LangGraph may return either a state-like object or a raw dict; normalize to ConversationState.
        result = self._graph.invoke(state)
        new_state = ConversationState.model_validate(result) if isinstance(result, dict) else result

        finalize_assistant_message(new_state)
        self._store.set(new_state)
        return new_state

    def reset(self, session_id: str) -> None:
        """
        Clear all stored state for a session.
        """
        self._store.reset(session_id)
