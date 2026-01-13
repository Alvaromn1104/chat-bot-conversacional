from __future__ import annotations

import re
from typing import Optional

from app.llm.router_schema import CartAction, CartOp

_SPLIT_RE = re.compile(r"(?:,|;|\n|\s+\by\b\s+|\s+\band\b\s+)", flags=re.IGNORECASE)

_ADD_KEYWORDS = [
    "add", "añade", "anade", "añadir", "agrega", "mete", "pon", "quiero", "buy", "take", "purchase",
    "añademe", "añádeme", "anademe", "añadme", "anadme",
    "agregame", "agrégame","meteme","agregame","agrégame"
]
_REMOVE_KEYWORDS = ["remove", "quita", "quitar", "quítame", "quitame", "elimina", "saca", "borra", "delete", "drop"]


_ID_RE = re.compile(r"\b(?P<id>\d{3})\b", flags=re.IGNORECASE)

def parse_cart_commands_by_name(text: str) -> tuple[list[CartAction], list[tuple[CartOp, int, str]]]:
    """
    Returns:
      - actions_with_ids: list[CartAction]  (already resolved by 3-digit IDs)
      - name_actions: list[(op, qty, name_hint_text)]  (need resolution by search)
    """
    if not text:
        return [], []

    t = text.lower()
    parts = _SPLIT_RE.split(t)

    actions_with_ids: list[CartAction] = []
    name_actions: list[tuple[CartOp, int, str]] = []

    last_op: Optional[CartOp] = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        op = _detect_op(part)
        if op is None:
            op = last_op
        else:
            last_op = op

        if op is None:
            continue

        # If contains a 3-digit id, treat as ID action
        m_id = _ID_RE.search(part)
        if m_id:
            pid = int(m_id.group("id"))
            qty = _extract_qty(part) or 1
            actions_with_ids.append(CartAction(op=op, product_id=pid, qty=qty))
            continue

        # Otherwise, treat as name hint action
        qty = _extract_qty(part) or 1
        # remove obvious op words + qty so the hint is cleaner
        hint = re.sub(r"\b\d+\b", " ", part)
        for k in _ADD_KEYWORDS + _REMOVE_KEYWORDS:
            hint = hint.replace(k, " ")
        hint = re.sub(r"\s+", " ", hint).strip()

        if hint:
            name_actions.append((op, qty, hint))

    return actions_with_ids, name_actions


def _detect_op(fragment: str) -> Optional[CartOp]:
    if any(k in fragment for k in _REMOVE_KEYWORDS):
        return CartOp.REMOVE
    if any(k in fragment for k in _ADD_KEYWORDS):
        return CartOp.ADD
    return None


def _extract_qty(fragment: str) -> Optional[int]:
    m = re.search(r"\b(\d{1,2})\b", fragment)
    return int(m.group(1)) if m else None
