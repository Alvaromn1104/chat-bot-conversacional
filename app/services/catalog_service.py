from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.data.catalog_loader import load_catalog
from app.domain.product import Product


@lru_cache(maxsize=1)
def get_catalog() -> list[Product]:
    return load_catalog()


def get_product_by_id(product_id: int) -> Optional[Product]:
    catalog = get_catalog()
    return next((p for p in catalog if p.id == product_id), None)
