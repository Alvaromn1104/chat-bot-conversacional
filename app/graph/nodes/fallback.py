from __future__ import annotations

from app.engine.state import ConversationState, Mode


from app.ux import t  # si quieres textos por idioma

def echo_node(state: ConversationState) -> ConversationState:
    # ✅ NO pisar si ya decidiste finalizar
    if state.should_end or state.mode == Mode.END:
        return state

    # ✅ NO pisar si una regla ya ha seteado un mensaje (out_of_scope, clarificaciones, etc.)
    if (state.assistant_message or "").strip():
        return state

    # fallback “echo” real
    state.assistant_message = f"(echo) {state.user_message}"
    return state