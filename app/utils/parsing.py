from __future__ import annotations

import re
from typing import Optional


# Patterns to extract (qty, product_id) across EN/ES phrasing.
_QTY_ID_PATTERNS: list[str] = [
    # EN: "add 2 of 310", "remove 3 x 310"
    r"\b(?P<qty>\d+)\s*(?:x|of)\s*(?P<id>\d{3})\b",
    # ES: "añade 2 del 310", "quita 3 de 310"
    r"\b(?P<qty>\d+)\s*(?:del|de)\s*(?P<id>\d{3})\b",
]

# Product IDs are represented as 3-digit numbers in this catalog.
_ID_ONLY_PATTERN = r"\b(?P<id>\d{3})\b"


def parse_qty_and_product_id(text: str) -> tuple[Optional[int], Optional[int]]:
    """
    Extract (qty, product_id) from free-text.

    Returns:
    - (qty, product_id) when both are present
    - (None, product_id) when only a product id is present
    - (None, None) when nothing matches
    """
    t = (text or "").lower()

    for pat in _QTY_ID_PATTERNS:
        m = re.search(pat, t)
        if m:
            return int(m.group("qty")), int(m.group("id"))

    m2 = re.search(_ID_ONLY_PATTERN, t)
    if m2:
        return None, int(m2.group("id"))

    return None, None


def parse_qty_only(text: str) -> Optional[int]:
    """
    Extract a standalone quantity from free-text when no product_id is present.

    Heuristics:
    - only accept 1-2 digit quantities (1..99) to avoid matching 3-digit product IDs
    - support formats like: "x2", "2 unidades", "2 units", "2 pcs", or plain "2"
    """
    t = (text or "").lower()

    # "x2"
    m = re.search(r"\bx\s*(\d{1,2})\b", t)
    if m:
        return int(m.group(1))

    # "2 unidades" / "2 unit" / "2 pcs"
    m = re.search(r"\b(\d{1,2})\s*(?:unidades?|units?|pcs?)\b", t)
    if m:
        return int(m.group(1))

    # Plain number (1-2 digits).
    m = re.search(r"\b(\d{1,2})\b", t)
    if m:
        return int(m.group(1))

    return None


def parse_adjustment(text: str) -> tuple[Optional[int], Optional[str]]:
    """
    Parse quantity adjustment requests.

    Examples:
    - "mejor que sea 1"
    - "solo 1"
    - "make it 2"
    - "just 1"
    - "change it to 3"

    Returns:
    - (target_qty, product_hint_text_or_none)
    """
    t = (text or "").lower().strip()
    if not t:
        return None, None

    # Keywords indicating the user is adjusting a previously discussed quantity.
    INTENT_KEYWORDS = [
        # ES
        "mejor", "solo", "que sea", "cámbialo", "cambialo", "en vez de",
        # EN
        "make it", "just", "only", "change it", "set it", "instead of", "better",
    ]

    if not any(k in t for k in INTENT_KEYWORDS):
        return None, None

    qty = parse_qty_only(t)
    if qty is None:
        return None, None

    # Remove the quantity token from the hint text.
    hint = re.sub(rf"\b{qty}\b", " ", t)
    hint = re.sub(r"\s+", " ", hint).strip()

    # Common weak words to reduce noise in the remaining hint.
    WEAK_WORDS = {
        # ES
        "mejor", "solo", "que", "sea", "sean", "cámbialo", "cambialo",
        "en", "vez", "de", "uno", "una",
        # EN
        "make", "it", "just", "only", "change", "set", "to", "instead", "of",
        "one",
    }

    tokens = [x for x in hint.split() if x and x not in WEAK_WORDS]
    product_hint = " ".join(tokens).strip() or None

    return qty, product_hint
