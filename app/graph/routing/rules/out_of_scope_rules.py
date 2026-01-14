from __future__ import annotations

from app.engine.state import ConversationState
from app.ux import t


def rule_out_of_scope(state: ConversationState) -> bool:
    """
    Fallback rule for unsupported or out-of-scope user requests.

    This rule always responds with a predefined message and ends the routing
    chain for the current turn.
    """
    state.assistant_message = t(state, "out_of_scope")
    state.next_node = "echo"
    return True
