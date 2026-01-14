from __future__ import annotations

import re
from typing import Optional

from app.llm.router_schema import CartAction, CartOp


"""
Deterministic cart command parsing by name and/or product id.

This parser supports multi-action messages (ES/EN), splitting the input into
segments and extracting cart operations as either:
- actions_with_ids: operations already resolved by a 3-digit product id
- name_actions: operations that require name resolution via search
"""

# Split input on common separators (punctuation, newline, and ES/EN conjunctions).
_SPLIT_RE = re.compile(r"(?:,|;|\n|\s+\by\b\s+|\s+\band\b\s+)", flags=re.IGNORECASE)

# Keywords used to infer cart operation from natural language fragments.
_ADD_KEYWORDS = [
    "add", "añade", "anade", "añadir", "agrega", "mete", "pon", "quiero", "buy", "take", "purchase",
    "añademe", "añádeme", "anademe", "añadme", "anadme",
    "agregame", "agrégame", "meteme", "agregame", "agrégame",
]
_REMOVE_KEYWORDS = [
    "remove", "quita", "quitar", "quítame", "quitame", "elimina", "saca", "borra", "delete", "drop",
]

# Product IDs are represented as 3-digit numbers in this catalog.
_ID_RE = re.compile(r"\b(?P<id>\d{3})\b", flags=re.IGNORECASE)


def parse_cart_commands_by_name(text: str) -> tuple[list[CartAction], list[tuple[CartOp, int, str]]]:
    """
    Parse cart operations from a user message.

    Returns:
      - actions_with_ids: list[CartAction]
        Operations already resolved via a 3-digit product id.

      - name_actions: list[(op, qty, name_hint_text)]
        Operations that require name-based resolution via search.
    """
    if not text:
        return [], []

    lower_text = text.lower()
    parts = _SPLIT_RE.split(lower_text)

    actions_with_ids: list[CartAction] = []
    name_actions: list[tuple[CartOp, int, str]] = []

    last_op: Optional[CartOp] = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # If the fragment doesn't contain an explicit op, reuse the last detected op.
        op = _detect_op(part)
        if op is None:
            op = last_op
        else:
            last_op = op

        if op is None:
            continue

        # If a 3-digit product id is present, treat the action as already resolved.
        m_id = _ID_RE.search(part)
        if m_id:
            pid = int(m_id.group("id"))
            qty = _extract_qty(part) or 1
            actions_with_ids.append(CartAction(op=op, product_id=pid, qty=qty))
            continue

        # Otherwise, interpret the fragment as a name-based hint.
        qty = _extract_qty(part) or 1

        # Remove obvious op words and numeric tokens to keep the hint clean for search.
        hint = re.sub(r"\b\d+\b", " ", part)
        for k in _ADD_KEYWORDS + _REMOVE_KEYWORDS:
            hint = hint.replace(k, " ")
        hint = re.sub(r"\s+", " ", hint).strip()

        if hint:
            name_actions.append((op, qty, hint))

    return actions_with_ids, name_actions


def _detect_op(fragment: str) -> Optional[CartOp]:
    """
    Infer the cart operation (add/remove) from a text fragment.
    """
    if any(k in fragment for k in _REMOVE_KEYWORDS):
        return CartOp.REMOVE
    if any(k in fragment for k in _ADD_KEYWORDS):
        return CartOp.ADD
    return None


def _extract_qty(fragment: str) -> Optional[int]:
    """
    Extract a 1-2 digit quantity from the fragment (if present).
    """
    m = re.search(r"\b(\d{1,2})\b", fragment)
    return int(m.group(1)) if m else None
