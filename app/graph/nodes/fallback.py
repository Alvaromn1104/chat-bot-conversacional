from __future__ import annotations

from app.engine.state import ConversationState, Mode


def echo_node(state: ConversationState) -> ConversationState:
    """
    Final fallback node.

    This node only sets a response when no other node/rule has produced one.
    """
    # Do not override an explicit end-of-conversation decision.
    if state.should_end or state.mode == Mode.END:
        return state

    # Do not override messages produced by other rules/nodes (clarifications, out-of-scope, etc.).
    if (state.assistant_message or "").strip():
        return state

    # Debug-style fallback echo (kept intentionally for the challenge flow).
    state.assistant_message = f"(echo) {state.user_message}"
    return state
