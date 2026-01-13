from __future__ import annotations

from typing import Optional

from app.domain.product import Product
from app.services.catalog_service import get_catalog, get_product_by_id


def tool_list_catalog() -> list[Product]:
    return get_catalog()


def tool_get_product(product_id: int) -> Optional[Product]:
    return get_product_by_id(product_id)
