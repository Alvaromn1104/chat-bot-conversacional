# tests/test_cart_tools.py
from app.engine.state import ConversationState
from app.tools import tool_add_to_cart, tool_remove_from_cart, tool_set_cart_qty, tool_cart_total


def test_add_to_cart_updates_cart_and_total():
    state = ConversationState(session_id="s1")

    ok, added = tool_add_to_cart(state, product_id=301, qty=2)
    assert ok is True
    assert added >= 1

    total = tool_cart_total(state)
    assert total > 0.0


def test_remove_from_cart_decrements_quantity_when_qty_remains():
    state = ConversationState(session_id="s1")

    tool_add_to_cart(state, product_id=301, qty=2)

    ok, removed = tool_remove_from_cart(state, product_id=301, qty=1)
    assert ok is True
    assert removed == 1

    item = next((x for x in state.cart if x.product_id == 301), None)
    assert item is not None
    assert item.qty == 1


def test_set_cart_qty_zero_removes_item():
    state = ConversationState(session_id="s1")
    tool_add_to_cart(state, product_id=301, qty=2)

    ok, new_qty = tool_set_cart_qty(state, product_id=301, qty=0)
    assert ok is True
    assert new_qty == 0

    assert all(x.product_id != 301 for x in state.cart)
