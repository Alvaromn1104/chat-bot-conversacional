from __future__ import annotations

from typing import Dict, Optional

from .state import ConversationState


class InMemorySessionStore:
    """
    Minimal in-memory session store.

    - Key: session_id
    - Value: ConversationState

    This implementation is intentionally simple and intended
    for development and testing purposes.
    """
    def __init__(self) -> None:
        self._db: Dict[str, ConversationState] = {}

    def get(self, session_id: str) -> Optional[ConversationState]:
        """
        Retrieve the conversation state for a given session.

        Returns None if the session does not exist.
        """
        return self._db.get(session_id)

    def set(self, state: ConversationState) -> None:
        """
        Persist the conversation state for a session.
        """
        self._db[state.session_id] = state

    def reset(self, session_id: str) -> None:
        """
        Remove the stored state for a given session.
        """
        self._db.pop(session_id, None)
