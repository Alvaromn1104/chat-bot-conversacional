from __future__ import annotations

from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.llm.router_schema import CartAction
from app.domain.product import Product


class CartItem(BaseModel):
    """A single cart line item (product + quantity)."""
    product_id: int
    qty: int = Field(default=1, ge=1)


class Mode(str, Enum):
    """
    High-level phase of the shopping flow.

    This acts as a coarse state machine for the conversation and is used
    to drive conditional routing within the graph.
    """
    CATALOG = "catalog"
    CART = "cart"
    CHECKOUT_CONFIRM = "checkout_confirm"
    COLLECT_SHIPPING = "collect_shipping"
    CHECKOUT_REVIEW = "checkout_review"
    END = "end"


class ShippingInfo(BaseModel):
    """
    Shipping/billing information collected from the user via a UI form.
    """
    full_name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None

    def is_complete(self) -> bool:
        """Returns True if all required shipping fields are present."""
        return bool(
            self.full_name
            and self.address_line1
            and self.city
            and self.postal_code
            and self.phone
        )


class ConversationState(BaseModel):
    """
    Single source of truth for the conversation.

    This state is passed through the graph on every turn and persisted by the engine.
    Fields are grouped by function: conversation, cart, routing, UI projection, and
    pending/resume operations.
    """

    # --- Session identity ---
    session_id: str

    # --- Core conversation fields ---
    mode: Mode = Mode.CATALOG
    user_message: str = ""
    assistant_message: str = ""

    # --- Checkout/shipping data ---
    shipping: ShippingInfo = Field(default_factory=ShippingInfo)

    # --- Conversation termination ---
    should_end: bool = False

    # --- Product selection and cart state ---
    selected_product_id: Optional[int] = None
    cart: list[CartItem] = Field(default_factory=list)

    # --- Router / intent metadata (useful for debugging and UX decisions) ---
    last_intent: str | None = None
    last_confidence: float = 0.0
    last_language: str | None = None

    # --- Graph control / routing hints ---
    next_node: str | None = None

    # --- Recommendation context ---
    recommended_family: Optional[list[str]] | None = None
    recommended_audience: str | None = None
    recommended_max_price: float | None = None
    recommended_min_price: float | None = None

    # --- Actions queued by the router/LLM to be executed by tools/nodes ---
    pending_actions: list[CartAction] = Field(default_factory=list)

    # --- UI projection (what the frontend needs to render) ---
    ui_products: list[Product] = Field(default_factory=list)
    ui_product: Product | None = None
    ui_cart_total: float | None = None

    ui_show_checkout_form: bool = False
    ui_form_error: str | None = None

    # --- User preferences ---
    preferred_language: str | None = None

    # --- Disambiguation / multi-step operations ---
    candidate_products: list[int] = Field(default_factory=list)
    pending_product_op: Literal["add", "remove", "set_qty", "detail"] | None = None
    pending_qty: int | None = None

    # --- Last cart operation metadata (used to avoid repetitive UX / confirm changes) ---
    last_cart_product_ids: list[int] = Field(default_factory=list)
    last_cart_op: Literal["add", "remove", "set_qty"] | None = None
    last_cart_qty: int | None = None

    # --- Resumable flows (e.g., name resolution / choice prompts) ---
    pending_name_actions: list[str] = Field(default_factory=list)
    resume_after_choice: str | None = None

    # --- Bulk operations / recommendation clarification flags ---
    pending_bulk_op: str | None = None
    pending_bulk_qty: int | None = None
    pending_recommend_clarification: bool = False
