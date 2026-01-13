from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Literal
from pathlib import Path
from dotenv import load_dotenv
from app.engine.service import ChatEngine
from app.engine.state import Mode
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

# Fuerza tu namespace de app a INFO (uvicorn a veces lo deja en WARNING)
logging.getLogger("app").setLevel(logging.INFO)

ENV_PATH = Path(__file__).resolve().with_name(".env")
load_dotenv(ENV_PATH, override=True)

app = FastAPI(title="E-commerce Cart Chatbot", version="0.1.0")

engine = ChatEngine()

class StartRequest(BaseModel):
    session_id: str = Field(min_length=1)
    language: Literal["es", "en"] | None = None

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    ui: dict[str, Any] = Field(default_factory=dict)

class ResetRequest(BaseModel):
    session_id: str

class CheckoutFormRequest(BaseModel):
    session_id: str
    full_name: str
    address_line1: str
    city: str
    postal_code: str
    phone: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    
    state = engine._store.get(req.session_id)
    if state and (state.should_end or state.mode == Mode.END):
        return ChatResponse(
            reply=state.assistant_message,
            ui={
                "should_end": True,
                "show_checkout_form": False,
                "form_error": None,
            },
        )
    state = engine.process_turn(session_id=req.session_id, user_message=req.message)

    ui_payload = {
        "products": [p.model_dump() for p in (state.ui_products or [])],
        "product": state.ui_product.model_dump() if state.ui_product else None,
        "cart": [item.model_dump() for item in state.cart],
        "cart_total": state.ui_cart_total,
        "mode": state.mode.value,
        "should_end": bool(state.should_end or state.mode == Mode.END),
        "show_checkout_form": state.ui_show_checkout_form,
        "form_error": state.ui_form_error,
    }

    return ChatResponse(reply=state.assistant_message, ui=ui_payload)

@app.post("/start", response_model=ChatResponse)
def start(req: StartRequest):
    state = engine.start_session(session_id=req.session_id, language=req.language)

    ui_payload = {
        "products": [p.model_dump() for p in (state.ui_products or [])],
        "product": state.ui_product.model_dump() if state.ui_product else None,
        "cart": [item.model_dump() for item in state.cart],
        "cart_total": state.ui_cart_total,
        "mode": state.mode.value,
        "show_checkout_form": state.ui_show_checkout_form,
        "form_error": state.ui_form_error,
        "should_end": bool(state.should_end or state.mode == Mode.END),
    }

    return ChatResponse(reply=state.assistant_message, ui=ui_payload)

@app.post("/reset")
def reset(req: ResetRequest):
    engine.reset(req.session_id)
    return {"status": "ok", "session_id": req.session_id}

@app.post("/checkout/submit", response_model=ChatResponse)
def checkout_submit(req: CheckoutFormRequest):
    state = engine.submit_checkout_form(
        session_id=req.session_id,
        full_name=req.full_name,
        address_line1=req.address_line1,
        city=req.city,
        postal_code=req.postal_code,
        phone=req.phone,
    )

    ui_payload = {
        "products": [p.model_dump() for p in (state.ui_products or [])],
        "product": state.ui_product.model_dump() if state.ui_product else None,
        "cart": [item.model_dump() for item in state.cart],
        "cart_total": state.ui_cart_total,
        "mode": state.mode.value,
        "should_end": bool(state.should_end or state.mode == Mode.END),
        "show_checkout_form": state.ui_show_checkout_form,
        "form_error": state.ui_form_error,
    }

    return ChatResponse(reply=state.assistant_message, ui=ui_payload)
