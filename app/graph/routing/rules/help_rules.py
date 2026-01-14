from __future__ import annotations

import re

from app.engine.state import ConversationState
from app.ux import t


# Detects explicit help requests in ES/EN.
# Kept as a regex to ensure deterministic routing without invoking the LLM.
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
    """
    Handle explicit help requests.

    When triggered, this rule responds immediately with a predefined help message
    and skips further graph execution for the current turn.
    """
    msg = (state.user_message or "").strip()
    if not msg:
        return False

    if not _HELP_RE.search(msg):
        return False

    state.assistant_message = t(state, "help_message")

    # End the turn after replying with help content.
    state.next_node = "echo"
    return True
