from __future__ import annotations

from app.engine.state import ConversationState, Mode


def route_node(state: ConversationState) -> ConversationState:
    """
    Routing passthrough node.

    This node exists to keep routing logic explicit in the graph and allows
    future extensions without changing the graph structure.
    """
    return state


def select_next_node(state: ConversationState) -> str:
    """
    Determine the next node to execute based on the current conversation state.

    Priority rules:
    - If the conversation has ended, always fall back to `echo`.
    - If an assistant message is already set and no explicit `next_node` is defined,
      avoid executing additional nodes.
    - Otherwise, route to `state.next_node` or default to `echo`.
    """

    # Hard stop: do not execute further nodes once the conversation is finished.
    if state.should_end or state.mode == Mode.END:
        return "echo"

    # If a response is already prepared and no explicit next step is defined,
    # skip further processing for this turn.
    if (state.assistant_message or "").strip() and not state.next_node:
        return "echo"

    return state.next_node or "echo"
