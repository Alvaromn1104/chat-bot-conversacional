from __future__ import annotations

from typing import Optional, List

from app.domain.product import Product
from app.services.recommend_service import recommend_products


def tool_recommend_products(
    families: Optional[List[str]],
    audience: Optional[str],
    max_price: Optional[float],
    min_price: Optional[float],
    limit: int = 3,
) -> list[Product]:
    return recommend_products(
        families=families,
        audience=audience,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
    )
