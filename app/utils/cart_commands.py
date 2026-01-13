from __future__ import annotations

import re
from typing import List, Optional

from app.llm.router_schema import CartAction, CartOp


# Split on common separators in EN / ES
# Example:
# "add 2 of 310, 1 of 302 and remove 1 of 307"
_SPLIT_RE = re.compile(
    r"(?:,|;|\n|\s+\by\b\s+|\s+\band\b\s+)",
    flags=re.IGNORECASE,
)

# Detect quantity + product id (quantity is optional)
# Valid examples:
# - "3 del 310"
# - "2 de 302"
# - "add 2 of 310"
# - "remove 3 x 310"
# - "310"  -> qty defaults to 1
_QTY_ID_RE = re.compile(
    r"\b(?:(?P<qty>\d+)\s*(?:x|of|del|de|units?|productos?)\s*)?(?P<id>\d{3})\b",
    flags=re.IGNORECASE,
)

# Keywords used to infer ADD operations
_ADD_KEYWORDS = [
    "add", "añade", "añademe", "añádeme", "agrega", "agrégame",
    "mete", "pon", "quiero", "llévame", "lleva", "buy", "take", "purchase",
]

# Keywords used to infer REMOVE operations
_REMOVE_KEYWORDS = [
    "remove", "quita", "quítame", "quitame", "quiteme", "elimina", "saca",
    "borra", "delete", "drop",
]


def parse_cart_commands(text: str) -> List[CartAction]:
    """
    Parse a user message into a list of cart actions (ADD / REMOVE).

    This deterministic parser supports "verb carry-over":
    if a fragment has no explicit operation verb, it inherits
    the last detected operation.
    """
    if not text:
        return []

    text = text.lower()
    parts = _SPLIT_RE.split(text)

    actions: List[CartAction] = []
    last_op: Optional[CartOp] = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        op = _detect_op(part)

        # Carry-over rule: inherit the last operation if none is present
        if op is None:
            op = last_op
        else:
            last_op = op

        if op is None:
            continue

        qty, product_id = _extract_qty_and_id(part)
        if product_id is None:
            continue

        actions.append(
            CartAction(
                op=op,
                product_id=product_id,
                qty=qty or 1,
            )
        )

    return actions


def _detect_op(fragment: str) -> Optional[CartOp]:
    """
    Detect whether a fragment represents an ADD or REMOVE operation.
    """
    if any(k in fragment for k in _REMOVE_KEYWORDS):
        return CartOp.REMOVE
    if any(k in fragment for k in _ADD_KEYWORDS):
        return CartOp.ADD
    return None


def _extract_qty_and_id(fragment: str) -> tuple[Optional[int], Optional[int]]:
    """
    Extract quantity and product id from a text fragment.
    """
    m = _QTY_ID_RE.search(fragment)
    if not m:
        return None, None

    qty = int(m.group("qty")) if m.group("qty") else None
    product_id = int(m.group("id"))

    return qty, product_id
