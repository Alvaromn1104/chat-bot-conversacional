from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class ApiConfig:
    base_url: str = "http://127.0.0.1:8000"
    session_id: str = "demo-session"
    language: str = "es"


def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    cfg = ApiConfig()

    start = _post(f"{cfg.base_url}/start", {"session_id": cfg.session_id, "language": cfg.language})
    print(start.get("reply", ""))
    print()

    while True:
        user_msg = input("You: ").strip()
        if not user_msg:
            continue

        data = _post(f"{cfg.base_url}/chat", {"session_id": cfg.session_id, "message": user_msg})
        print("\nBot:", data.get("reply", ""))
        print()

        ui = data.get("ui") or {}
        if ui.get("should_end") is True:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
