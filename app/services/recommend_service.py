from __future__ import annotations

from typing import Optional

from app.domain.product import Product
from app.services.catalog_service import get_catalog


def recommend_products(
    families: Optional[list[str]],
    audience: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    limit: int = 3,
) -> list[Product]:
    """
    Recommend products from the catalog based on user constraints.

    Strategy:
    1) Strict match: family + audience + price constraints.
    2) Relaxed audience (male/female -> allow unisex) while keeping family + price.
    3) No fallback to unrelated families or arbitrary "cheapest" items.

    Returning an empty list is intentional: the calling node can decide how to
    message the user (e.g., ask to relax constraints) without making assumptions.
    """
    catalog = get_catalog()

    norm_families = [f.strip().lower() for f in (families or []) if (f or "").strip()]

    def _family_ok(p: Product) -> bool:
        if not norm_families:
            return True
        pf = (p.family or "").strip().lower()
        return pf in norm_families

    def _matches(p: Product) -> bool:
        if not _family_ok(p):
            return False
        if audience and (p.audience or "").strip().lower() != audience.strip().lower():
            return False
        if min_price is not None and p.price < min_price:
            return False
        if max_price is not None and p.price > max_price:
            return False
        return True

    # 1) Strict: respect all constraints.
    strict = [p for p in catalog if _matches(p)]
    if strict:
        return sorted(strict, key=lambda x: x.price)[:limit]

    # 2) Relax audience (male/female -> allow unisex) while keeping family + price constraints.
    if audience in ("male", "female"):
        aud = audience.strip().lower()

        def _matches_relaxed_audience(p: Product) -> bool:
            if not _family_ok(p):
                return False
            if min_price is not None and p.price < min_price:
                return False
            if max_price is not None and p.price > max_price:
                return False
            return (p.audience or "").strip().lower() in (aud, "unisex")

        relaxed = [p for p in catalog if _matches_relaxed_audience(p)]
        if relaxed:
            return sorted(relaxed, key=lambda x: x.price)[:limit]

    # 3) No fallback to unrelated families or arbitrary "cheapest" items.
    # If no match exists, return [] and let the caller decide the next UX step.
    return []
