from __future__ import annotations

from typing import Optional

from app.domain.product import Product
from app.services.catalog_service import get_catalog, get_product_by_id


def tool_list_catalog() -> list[Product]:
    """
    Return the full product catalog.

    This tool provides read-only access to the catalog for graph nodes.
    """
    return get_catalog()


def tool_get_product(product_id: int) -> Optional[Product]:
    """
    Retrieve a single product by its identifier.

    Returns None if the product does not exist.
    """
    return get_product_by_id(product_id)
