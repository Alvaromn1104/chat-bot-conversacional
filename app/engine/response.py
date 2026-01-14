from __future__ import annotations

import re

from app.engine.state import ConversationState, Mode
from app.ux import t


# Used to remove emojis from responses in sensitive UX flows (e.g., checkout),
# where tone should remain neutral and unambiguous.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "]",
    flags=re.UNICODE,
)


def finalize_assistant_message(state: ConversationState) -> None:
    """
    Apply consistent UX rules to every assistant response.

    This is a post-processing step to keep responses predictable across nodes
    and avoid leaking formatting differences into the frontend.
    """
    if state.should_end or state.mode == Mode.END:
        return

    msg = (state.assistant_message or "").strip()
    if not msg:
        msg = t(state, "fallback_ok")

    # In checkout-related steps, avoid emojis to keep the message tone neutral
    # and reduce the risk of confusion in transactional flows.
    if state.mode in {
        Mode.CHECKOUT_CONFIRM,
        Mode.CHECKOUT_REVIEW,
        Mode.COLLECT_SHIPPING,
    }:
        msg = _EMOJI_RE.sub("", msg).strip()
        state.assistant_message = msg
        return

    follow_up = t(state, "follow_up")

    # Prevent duplicating the follow-up prompt when the message already includes it.
    if follow_up and follow_up.lower() in msg.lower():
        state.assistant_message = msg
        return

    state.assistant_message = f"{msg}\n\n{follow_up}"
