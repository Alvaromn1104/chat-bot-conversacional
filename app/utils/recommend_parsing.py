from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Normalizamos familias a los valores que usa tu catálogo / recommend_service
# (coinciden con el prompt del router y el JSON: citrus, woody, etc.)
_FAMILY_SYNONYMS: dict[str, str] = {
    # EN
    "woody": "woody",
    "wood": "woody",
    "citrus": "citrus",
    "fresh": "citrus",  # debatible, pero útil
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
    families: list[str]
    audience: Optional[str]
    min_price: Optional[float]
    max_price: Optional[float]

    def is_empty(self) -> bool:
        return not self.families and self.audience is None and self.min_price is None and self.max_price is None


def parse_recommend_slots(text: str, lang: str) -> RecommendSlots:
    """
    Heurístico: extrae slots de recomendación SIN LLM.
    Objetivo: robusto y explicable, no perfecto.

    - families: lista de familias (OR implícito)
    - audience: male/female/unisex
    - min_price / max_price: en EUR (float)
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
    raw = raw.strip().lower()
    if not raw:
        return False
    if " " in raw:
        return raw in t  # frases tipo "por menos de"
    return re.search(rf"\b{re.escape(raw)}\b", t) is not None


def _parse_families(t: str) -> list[str]:
    found: list[str] = []

    # Detect “X or Y” / “X o Y” by scanning tokens; we keep it simple:
    # if any synonym appears, add its normalized family.
    for raw, norm in _FAMILY_SYNONYMS.items():
        if _contains_token(t, raw):
         found.append(norm)

    # Dedup, preserve order
    out: list[str] = []
    seen: set[str] = set()
    for f in found:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _parse_audience(t: str) -> Optional[str]:
    # Prioridad: unisex explícito
    if re.search(r"\bunisex\b", t):
        return "unisex"

    # EN (word boundary) — evita que "man" haga match dentro de otras palabras
    if re.search(r"\bfor\s+men\b", t) or re.search(r"\bmen\b", t) or re.search(r"\bmale\b", t):
        return "male"

    if re.search(r"\bfor\s+women\b", t) or re.search(r"\bwomen\b", t) or re.search(r"\bfemale\b", t):
        return "female"

    # ES
    if re.search(r"\bpara\s+hombre\b", t) or re.search(r"\bhombre\b", t) or re.search(r"\bmasculino\b", t):
        return "male"

    if re.search(r"\bpara\s+mujer\b", t) or re.search(r"\bmujer\b", t) or re.search(r"\bfemenino\b", t):
        return "female"

    return None



def _parse_price_range(t: str) -> tuple[Optional[float], Optional[float]]:
    """
    Soporta:
    - under/below/less than / por menos de / menos de
    - over/more than / por más de / mas de / más de
    - between X and Y / entre X y Y / de X a Y
    - “100€” / “100 eur” etc.
    """
    # 1) Rango explícito: between/entre/de X a Y
    m = re.search(r"\b(?:between|entre|de)\s*(\d+(?:[.,]\d+)?)\s*(?:and|y|a)\s*(\d+(?:[.,]\d+)?)\b", t)
    if m:
        a = _to_float(m.group(1))
        b = _to_float(m.group(2))
        if a is not None and b is not None:
            return (min(a, b), max(a, b))

    # 2) Under / menos de / por debajo de
    m = re.search(r"\b(?:under|below|less than|menos de|por menos de|por debajo de)\s*(\d+(?:[.,]\d+)?)\b", t)
    if m:
        mx = _to_float(m.group(1))
        return (None, mx)

    # 3) Over / más de / por encima de
    m = re.search(r"\b(?:over|more than|mas de|más de|por encima de)\s*(\d+(?:[.,]\d+)?)\b", t)
    if m:
        mn = _to_float(m.group(1))
        return (mn, None)

    # 4) Si aparece “100€” o “100 eur”, lo tratamos como max_price (lo típico en recomendaciones)
    #    Esto evita que “woody 100” se quede sin rango.
    m = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:€|eur|euros?)\b", t)
    if m:
        mx = _to_float(m.group(1))
        return (None, mx)

    # 5) Si aparece “under 100” sin currency, ya lo pillamos arriba.
    #    Si aparece solo un número suelto, NO lo interpreto como precio para evitar falsos positivos.
    return (None, None)


def _to_float(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", "."))
    except Exception:
        return None
