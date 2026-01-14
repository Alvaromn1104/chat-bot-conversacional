# tests/test_checkout_flow.py
from app.engine.state import Mode


def test_checkout_confirmation_no_returns_to_cart(engine, session_id):
    engine.start_session(session_id)

    state = engine.process_turn(session_id, "añade 1 del 301")
    assert state.mode == Mode.CART

    state = engine.process_turn(session_id, "finalizar compra")
    assert state.mode == Mode.CHECKOUT_CONFIRM
    assert "¿quieres continuar" in (state.assistant_message or "").lower()

    state = engine.process_turn(session_id, "no")
    assert state.mode == Mode.CART
