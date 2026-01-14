from __future__ import annotations

from typing import Dict, Optional

from .state import ConversationState


class InMemorySessionStore:
    """
    Minimal in-memory session store.

    - Key: session_id
    - Value: ConversationState

    Notes:
    - This store is ephemeral (data is lost on process restart).
    - It is not shared across multiple worker processes/instances.
    - Suitable for local development and tests; production deployments
      typically require a shared persistent store (e.g., Redis/Postgres).
    """
    def __init__(self) -> None:
        # Internal in-memory map for session state.
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

        Overwrites any existing state for the same session_id.
        """
        self._db[state.session_id] = state

    def reset(self, session_id: str) -> None:
        """
        Remove the stored state for a given session.

        This operation is idempotent: resetting an unknown session_id is a no-op.
        """
        self._db.pop(session_id, None)
