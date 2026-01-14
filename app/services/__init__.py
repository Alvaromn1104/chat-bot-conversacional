from .catalog_service import get_catalog, get_product_by_id
from .cart_service import calculate_cart_total
from .recommend_service import recommend_products

"""
Public service interface for the application domain.

This module exposes a curated set of service functions used by the engine
and graph nodes, acting as a façade over the internal service implementations.
"""

__all__ = [
    "get_catalog",
    "get_product_by_id",
    "calculate_cart_total",
    "recommend_products",
]
