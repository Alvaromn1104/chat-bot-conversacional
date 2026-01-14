from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


"""
Deterministic recommendation slot parsing (no LLM).

Extracts structured constraints from user text:
- families (normalized to catalog values)
- audience (male/female/unisex)
- min_price / max_price (EUR)

This parser is heuristic by design: it aims to be robust and explainable,
not perfectly accurate.
"""

# Normalizes family synonyms to the canonical values used by the catalog/recommender.
_FAMILY_SYNONYMS: dict[str, str] = {
    # EN
    "woody": "woody",
    "wood": "woody",
    "citrus": "citrus",
    "fresh": "citrus",  # heuristic mapping
    "floral": "floral",
    "oriental": "oriental",
    "amber": "oriental",
    "aquatic": "aquatic",
    "marine": "aquatic",
    "aromatic": "aromatic",
    "gourmand": "gourmand",
    "sweet": "gourmand",
    "fruity": "fruity",
    "leather": "leather",
    # ES
    "amaderado": "woody",
    "amaderados": "woody",
    "maderoso": "woody",
    "maderosos": "woody",
    "citrico": "citrus",
    "cítrico": "citrus",
    "citricos": "citrus",
    "cítricos": "citrus",
    "floral": "floral",
    "florales": "floral",
    "oriental": "oriental",
    "orientales": "oriental",
    "ambar": "oriental",
    "ámbar": "oriental",
    "acuatico": "aquatic",
    "acuáticos": "aquatic",
    "acuaticos": "aquatic",
    "marino": "aquatic",
    "marinos": "aquatic",
    "aromatico": "aromatic",
    "aromático": "aromatic",
    "aromaticos": "aromatic",
    "aromáticos": "aromatic",
    "gourmand": "gourmand",
    "dulce": "gourmand",
    "dulces": "gourmand",
    "afrutado": "fruity",
    "afrutados": "fruity",
    "frutal": "fruity",
    "frutales": "fruity",
    "cuero": "leather",
}


@dataclass(frozen=True)
class RecommendSlots:
    """Structured recommendation constraints extracted from user text."""
    families: list[str]
    audience: Optional[str]
    min_price: Optional[float]
    max_price: Optional[float]

    def is_empty(self) -> bool:
        return (
            not self.families
            and self.audience is None
            and self.min_price is None
            and self.max_price is None
        )


def parse_recommend_slots(text: str, lang: str) -> RecommendSlots:
    """
    Extract recommendation slots from free-text.

    Note: `lang` is reserved for potential language-specific tuning. The current
    implementation relies on mixed ES/EN heuristics.
    """
    t = (text or "").lower().strip()
    if not t:
        return RecommendSlots(families=[], audience=None, min_price=None, max_price=None)

    families = _parse_families(t)
    audience = _parse_audience(t)
    min_price, max_price = _parse_price_range(t)

    return RecommendSlots(
        families=families,
        audience=audience,
        min_price=min_price,
        max_price=max_price,
    )


def _contains_token(t: str, raw: str) -> bool:
    """
    Check whether `raw` appears in text as a token (or full phrase).
    """
    raw = raw.strip().lower()
    if not raw:
        return False
    if " " in raw:
        return raw in t
    return re.search(rf"\b{re.escape(raw)}\b", t) is not None


def _parse_families(t: str) -> list[str]:
    """
    Extract normalized olfactory families from text, preserving first-seen order.
    """
    found: list[str] = []

    for raw, norm in _FAMILY_SYNONYMS.items():
        if _contains_token(t, raw):
            found.append(norm)

    out: list[str] = []
    seen: set[str] = set()
    for f in found:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _parse_audience(t: str) -> Optional[str]:
    """Extract audience intent (male/female/unisex) from text."""
    if re.search(r"\bunisex\b", t):
        return "unisex"

    if re.search(r"\bfor\s+men\b", t) or re.search(r"\bmen\b", t) or re.search(r"\bmale\b", t):
        return "male"

    if re.search(r"\bfor\s+women\b", t) or re.search(r"\bwomen\b", t) or re.search(r"\bfemale\b", t):
        return "female"

    if re.search(r"\bpara\s+hombre\b", t) or re.search(r"\bhombre\b", t) or re.search(r"\bmasculino\b", t):
        return "male"

    if re.search(r"\bpara\s+mujer\b", t) or re.search(r"\bmujer\b", t) or re.search(r"\bfemenino\b", t):
        return "female"

    return None


def _parse_price_range(t: str) -> tuple[Optional[float], Optional[float]]:
    """
    Extract a (min_price, max_price) tuple from text.

    Supports:
    - under/below/less than / menos de / por menos de / por debajo de
    - over/more than / mas de / más de / por encima de
    - between X and Y / entre X y Y / de X a Y
    - "100€" / "100 eur" style mentions
    """
    m = re.search(r"\b(?:between|entre|de)\s*(\d+(?:[.,]\d+)?)\s*(?:and|y|a)\s*(\d+(?:[.,]\d+)?)\b", t)
    if m:
        a = _to_float(m.group(1))
        b = _to_float(m.group(2))
        if a is not None and b is not None:
            return (min(a, b), max(a, b))

    m = re.search(r"\b(?:under|below|less than|menos de|por menos de|por debajo de)\s*(\d+(?:[.,]\d+)?)\b", t)
    if m:
        mx = _to_float(m.group(1))
        return (None, mx)

    m = re.search(r"\b(?:over|more than|mas de|más de|por encima de)\s*(\d+(?:[.,]\d+)?)\b", t)
    if m:
        mn = _to_float(m.group(1))
        return (mn, None)

    m = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)\b", t)
    if m:
        mx = _to_float(m.group(1))
        return (None, mx)

    return (None, None)


def _to_float(s: str) -> Optional[float]:
    """Convert a localized numeric string to float (comma or dot decimals)."""
    try:
        return float(s.replace(",", "."))
    except Exception:
        return None
