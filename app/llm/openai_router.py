from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from app.engine.state import ConversationState
from app.llm.router_schema import RouterResult, Intent


def _build_system_prompt() -> str:
    """
    System prompt for routing and slot extraction.

    The model must return ONLY valid JSON matching RouterResult.
    No extra keys. No extra text.
    """
    return (
        "You are an intent router for a perfume e-commerce chatbot.\n"
        "Your job: classify the user's intent and extract structured fields.\n"
        "Return ONLY valid JSON. No extra text. No markdown.\n"
        "Do NOT invent prices, stock, or product details.\n\n"

        "IMPORTANT:\n"
        "- If the message contains MULTIPLE cart operations (e.g., add X of 310 AND remove Y of 307),\n"
        "  you MUST set intent = \"bulk_cart_update\" and fill the actions[] array.\n"
        "- If there is ONLY ONE cart operation, use intent = \"add_to_cart\" or \"remove_from_cart\" and keep actions = [].\n\n"

        "Supported intents:\n"
        "- show_catalog\n"
        "- show_product_detail\n"
        "- add_to_cart\n"
        "- remove_from_cart\n"
        "- view_cart\n"
        "- checkout_confirm\n"
        "- recommend_product\n"
        "- bulk_cart_update\n"
        "- end\n"
        "- unknown\n\n"

        "Field extraction rules:\n"
        "- product_id: if the user message contains a 3-digit number (e.g., 301), extract it.\n"
        "- For single cart actions:\n"
        "  - add/buy/take -> intent = add_to_cart\n"
        "  - remove/delete -> intent = remove_from_cart\n"
        "- If the user asks to see the cart -> intent = view_cart\n"
        "- If the user wants to pay/checkout -> intent = checkout_confirm\n"
        "- If the user asks for recommendations -> intent = recommend_product\n\n"
        "- If the user asks to see a specific product/brand by name (even without a 3-digit id), set intent = \"show_product_detail\" and keep product_id = null.\n\n"
        " If the user wants to end the conversation (e.g., \"salir\", \"finalizar\", \"terminar\", \"exit\", \"quit\", \"bye\"), set intent = \"end\"."

        "Multi-action cart extraction (actions[]):\n"
        "- actions is an array of objects.\n"
        "- Each action has: op, product_id, qty.\n"
        "- op is one of: \"add\", \"remove\".\n"
        "- qty defaults to 1 if not specified.\n"
        "- Keep the same order as in the user's text.\n"
        "- Examples of multi-action:\n"
        "  - \"Add 2 of 310 and remove 1 of 307\" -> 2 actions\n"
        "  - \"Añade 3 del 310, 2 del 302 y quita 1 del 307\" -> 3 actions\n\n"

        "Recommendation slots (recommend_product):\n"
        "- family: return an ARRAY of families (strings).\n"
        "  Allowed values: citrus, woody, oriental, floral, aquatic, aromatic, gourmand, fruity, leather.\n"
        "  If user says 'X or Y' / 'X o Y', include both (e.g., [\"woody\",\"citrus\"]).\n"
        "  If only one family is requested, use a single-item array (e.g., [\"woody\"]).\n"
        "- audience: male, female, unisex when implied.\n"
        "- max_price: if the user mentions a budget (e.g., under 100), set max_price.\n"
        "- min_price: if the user mentions a minimum budget (e.g., over 100, more than 80, superior a 100), set min_price.\n"
        "- price range: if the user asks for a range (e.g., between 100 and 150, entre 100 y 150, de 100 a 150), set min_price and max_price accordingly.\n\n"

        "Detect language:\n"
        "- language: \"es\" for Spanish, \"en\" for English.\n\n"

        "Spanish examples:\n"
        "- '¿Qué perfumes tenéis?' -> show_catalog\n"
        "- 'Enséñame el 301' -> show_product_detail + product_id=301\n"
        "- 'Añade el 301 al carrito' -> add_to_cart + product_id=301\n"
        "- 'Muéstrame el carrito' -> view_cart\n"
        "- 'Quítalo del carrito' -> remove_from_cart\n"
        "- 'Recomiéndame algo cítrico para verano por menos de 100€' -> recommend_product + family=citrus + max_price=100\n"
        "- 'Añade 3 del 310, 2 del 302 y quita 1 del 307' -> bulk_cart_update + actions\n\n"
        "- 'Recomiéndame perfumes amaderados o cítricos por más de 100€' -> "
        "recommend_product + family=[woody,citrus] + min_price=100\n"

        "Output JSON schema (keys must exist, use null when unknown):\n"
        "{\n"
        "  \"intent\": \"show_catalog|show_product_detail|add_to_cart|remove_from_cart|view_cart|checkout_confirm|recommend_product|bulk_cart_update |end|unknown\",\n"
        "  \"confidence\": 0.0,\n"
        "  \"language\": \"en|es|null\",\n"
        "  \"product_id\": 301,\n"
        "  \"name\": null,\n"
        "  \"city\": null,\n"
        "  \"family\": [\"citrus\", \"woody\"],\n"
        "  \"audience\": null,\n"
        "  \"max_price\": null,\n"
        "  \"min_price\": null,\n"
        "  \"actions\": [\n"
        "    {\"op\":\"add\",\"product_id\":310,\"qty\":2},\n"
        "    {\"op\":\"remove\",\"product_id\":307,\"qty\":1}\n"
        "  ]\n"
        "}\n\n"

        "Rules:\n"
        "- Return ONLY the JSON object.\n"
        "- Do NOT include any extra keys.\n"
        "- For single-intent flows, actions MUST be [].\n"
    )


def _build_user_context(state: ConversationState) -> str:
    """
    Build a compact JSON context payload for the router.

    The context is intentionally minimal to reduce token usage while still
    providing the router with flow-critical information.
    """
    shipping = getattr(state, "shipping", None)

    payload = {
        "mode": getattr(state.mode, "value", str(state.mode)),
        "user_message": state.user_message,
        "selected_product_id": state.selected_product_id,
        "cart_size": len(state.cart),
        "shipping_full_name_present": bool(getattr(shipping, "full_name", None)),
        "shipping_address_present": bool(getattr(shipping, "address_line1", None)),
        "shipping_city_present": bool(getattr(shipping, "city", None)),
        "shipping_postal_code_present": bool(getattr(shipping, "postal_code", None)),
        "shipping_phone_present": bool(getattr(shipping, "phone", None)),
        "ui_show_checkout_form": bool(getattr(state, "ui_show_checkout_form", False)),
    }
    return json.dumps(payload, ensure_ascii=False)


def _extract_json(text: str) -> dict[str, Any]:
    """
    Defensive JSON extraction from model output.

    Even with structured response formatting enabled, this guards against
    edge cases where the model returns additional text around a JSON object.
    """
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model output.")
    return json.loads(m.group(0))


def interpret_with_openai(state: ConversationState) -> RouterResult:
    """
    Run intent routing and slot extraction via OpenAI.

    If OPENAI_API_KEY is not set, the router degrades gracefully to UNKNOWN.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return RouterResult(intent=Intent.UNKNOWN, confidence=0.0)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    schema = RouterResult.model_json_schema()
    schema["additionalProperties"] = False

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": state.user_message},
            {"role": "user", "content": f"Context: {_build_user_context(state)}"},
        ],
        response_format={"type": "json_object"},
    )

    text = resp.choices[0].message.content or "{}"
    data = _extract_json(text)
    return RouterResult.model_validate(data)
