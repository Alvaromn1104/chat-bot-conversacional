from __future__ import annotations

import re
from typing import List

from app.domain.product import Product
from app.tools.catalog_tools import tool_list_catalog

_STOPWORDS = {
    # ES
    "añade", "anade", "añadir", "agrega", "mete", "pon", "quita", "quitar",
    "borra", "elimina", "del", "de", "al", "el", "la", "los", "las",
    "un", "una", "unos", "unas", "carrito", "por", "favor", "quiero",
    "añademe", "añádeme", "anademe",
    # EN
    "add", "remove", "delete", "put", "set", "to", "the", "a", "an", "cart",
    "show", "me", "my", "please", "pls", "ur", "u", "want", "would", "like",
}

def tool_find_products_by_name(query: str, limit: int = 5) -> List[int]:
    """
    Returns product IDs whose brand/name match tokens extracted from the query.
    Returns ONLY the best-scoring matches (ties allowed).
    """
    text = (query or "").lower().strip()
    if not text:
        return []

    # Remove numbers (ids/qty) and punctuation, keep words
    text = re.sub(r"\b\d+\b", " ", text)
    tokens = [t for t in re.split(r"\s+", text) if t and t not in _STOPWORDS]

    # ✅ ignore tiny tokens to avoid false positives ("la", "de", "me", etc.)
    tokens = [t for t in tokens if len(t) >= 3]

    if not tokens:
        return []

    catalog = tool_list_catalog()

    # ✅ If it's a single token, try strong match on brand first
    if len(tokens) == 1:
        tok = tokens[0]
        brand_hits = [p.id for p in catalog if (p.brand or "").lower() == tok]
        if brand_hits:
            return brand_hits[:limit]

    scored: list[tuple[int, Product]] = []

    for p in catalog:
        hay = f"{p.brand or ''} {p.name}".lower()

        # token-in-hay scoring
        score = sum(1 for tok in tokens if tok in hay)
        if score > 0:
            scored.append((score, p))

    if not scored:
        return []

    scored.sort(key=lambda x: x[0], reverse=True)

    best_score = scored[0][0]
    best = [p.id for s, p in scored if s == best_score]

    return best[:limit]
