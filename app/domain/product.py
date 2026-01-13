from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    """
    Domain model representing a product in the catalog.

    In this project, a Product models a perfume with optional attributes
    that enable filtering, recommendations, and conversational queries.
    """
    id: int
    name: str
    price: float = Field(ge=0)
    category: str | None = "perfumes"
    description: str | None = None
    description_es: str | None = None
    brand: str | None = None
    concentration: str | None = None   # e.g. "EDT", "EDP", "Parfum"
    size_ml: int | None = Field(default=None, gt=0)
    family: str | None = None          # e.g. "citrus", "woody", "oriental", etc.
    audience: str | None = None        # e.g. "male", "female", "unisex"
    stock: int = Field(default=0, ge=0)
    img: str | None = None
