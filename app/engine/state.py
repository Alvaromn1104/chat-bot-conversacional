from __future__ import annotations

from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.llm.router_schema import CartAction
from app.domain.product import Product


class CartItem(BaseModel):
    product_id: int
    qty: int = Field(default=1, ge=1)


class Mode(str, Enum):
    """
    Represents the current high-level phase of the shopping flow.
    """
    CATALOG = "catalog"
    CART = "cart"
    CHECKOUT_CONFIRM = "checkout_confirm"
    COLLECT_SHIPPING = "collect_shipping"
    CHECKOUT_REVIEW = "checkout_review"
    END = "end"


class ShippingInfo(BaseModel):
    """
    More realistic billing/shipping info collected via UI popup (Gradio).
    """
    full_name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None

    def is_complete(self) -> bool:
        return bool(
            self.full_name
            and self.address_line1
            and self.city
            and self.postal_code
            and self.phone
        )


class ConversationState(BaseModel):
    session_id: str

    mode: Mode = Mode.CATALOG
    user_message: str = ""
    assistant_message: str = ""

    shipping: ShippingInfo = Field(default_factory=ShippingInfo)

    should_end: bool = False
    selected_product_id: Optional[int] = None
    cart: list[CartItem] = Field(default_factory=list)

    last_intent: str | None = None
    last_confidence: float = 0.0
    last_language: str | None = None

    next_node: str | None = None
    recommended_family: Optional[list[str]] | None = None
    recommended_audience: str | None = None
    recommended_max_price: float | None = None
    recommended_min_price: float | None = None
    pending_actions: list[CartAction] = Field(default_factory=list)

    ui_products: list[Product] = Field(default_factory=list)
    ui_product: Product | None = None
    ui_cart_total: float | None = None

    ui_show_checkout_form: bool = False
    ui_form_error: str | None = None

    preferred_language: str | None = None

    candidate_products: list[int] = Field(default_factory=list)
    pending_product_op: Literal["add", "remove", "set_qty", "detail"] | None = None
    pending_qty: int | None = None

    last_cart_product_ids: list[int] = Field(default_factory=list)
    last_cart_op: Literal["add", "remove", "set_qty"] | None = None
    last_cart_qty: int | None = None

    pending_name_actions: list[str] = Field(default_factory=list)
    resume_after_choice: str | None = None

    pending_bulk_op: str | None = None
    pending_bulk_qty: int | None = None
    pending_recommend_clarification: bool = False
