from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

class CartOp(str, Enum):
    """
    Supported cart operations.
    """
    ADD = "add"
    REMOVE = "remove"


class CartAction(BaseModel):
    """
    A single cart operation extracted from user input.
    """
    op: CartOp
    product_id: int = Field(ge=100, le=999)
    qty: int = Field(default=1, ge=1)

class Intent(str, Enum):
    """
    Supported intents for the e-commerce assistant.
    """
    SHOW_CATALOG = "show_catalog"
    SHOW_PRODUCT_DETAIL = "show_product_detail"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    VIEW_CART = "view_cart"
    CHECKOUT = "checkout_confirm"
    CONFIRM_YES = "confirm_yes"
    CONFIRM_NO = "confirm_no"
    PROVIDE_NAME = "provide_name"
    PROVIDE_CITY = "provide_city"
    RECOMMEND_PRODUCT = "recommend_product"
    UNKNOWN = "unknown"
    BULK_CART_UPDATE = "bulk_cart_update"
    END = "end"


class RouterResult(BaseModel):
    """
    Structured interpretation of a user message.

    This output is used to drive LangGraph routing deterministically.
    """
    intent: Intent = Intent.UNKNOWN
    product_id: Optional[int] = Field(default=None, description="3-digit product ID when applicable")
    name: Optional[str] = None
    city: Optional[str] = None
    family: Optional[list[str]] = Field(default=None, description="Olfactory family, e.g. citrus, woody, oriental, floral, aquatic, aromatic, gourmand, fruity, leather")
    audience: Optional[str] = Field(default=None, description="Target audience: male, female, unisex")
    max_price: Optional[float] = Field(default=None, ge=0.0, description="Maximum price in EUR")
    min_price: Optional[float] = Field(default=None, ge=0.0, description="Minimun price in EUR")
    language: Optional[str] = Field(default=None, description="ISO-like language hint, e.g. 'en' or 'es'")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    actions: list[CartAction] = Field(default_factory=list)
    
