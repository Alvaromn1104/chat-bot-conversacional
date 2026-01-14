# app/tests/conftest.py
import os
import sys
import pytest

# Ensure project root is importable when running tests directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.engine.service import ChatEngine


@pytest.fixture(autouse=True)
def disable_llm(monkeypatch):
    monkeypatch.setenv("LLM_ROUTER_ENABLED", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture()
def engine():
    return ChatEngine()


@pytest.fixture()
def session_id():
    return "test-session"
