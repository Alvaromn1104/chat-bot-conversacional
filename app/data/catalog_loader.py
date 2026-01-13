from __future__ import annotations

import json
from pathlib import Path

from app.domain.product import Product

CATALOG_PATH = Path(__file__).with_name("catalog.json")


def load_catalog() -> list[Product]:
    """
    Loads the perfume catalog from a JSON file and validates it against the Product model.

    Rationale:
    - Centralizes access to the catalog (nodes should not read JSON files directly).
    - Performs runtime validation using Pydantic to prevent corrupted catalog data.
    """
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [Product.model_validate(item) for item in data]
