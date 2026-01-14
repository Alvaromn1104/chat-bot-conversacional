# tests/test_graph_behavior.py
from app.engine.state import Mode


def test_remove_qty_only_prompts_for_product_choice_when_cart_has_multiple_items(engine, session_id):
    state = engine.start_session(session_id)

    state = engine.process_turn(session_id, "añademe 1 del 319 y 1 del 312")
    assert state.mode in (Mode.CART, Mode.CATALOG)

    state = engine.process_turn(session_id, "quitame 1")

    msg = (state.assistant_message or "").lower()
    assert "¿cuál quieres quitar" in msg or "cual quieres quitar" in msg

    assert state.pending_product_op == "remove"
    assert state.pending_qty == 1
    assert len(state.candidate_products) >= 2
