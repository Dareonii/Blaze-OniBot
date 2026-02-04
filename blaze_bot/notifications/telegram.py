from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id

    def send_message(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        response = requests.post(url, json={"chat_id": self.chat_id, "text": text}, timeout=10)
        response.raise_for_status()

    def prediction(self, prediction: Dict[str, Any]) -> None:
        color = prediction.get("color", "-")
        strategy = prediction.get("strategy")
        suffix = f" ({strategy})" if strategy else ""
        self.send_message(f"🎯 Blaze Double\nEntrada: {color}{suffix}")

    def evaluation(self, win: bool, result: Dict[str, Any], winrate: float) -> None:
        status = "✅" if win else "❌"
        message = (
            "🎯 Blaze Double\n"
            f"Resultado: {result['color']} ({result['number']}) {status}\n"
            f"Winrate atual: {winrate:.2f}%"
        )
        self.send_message(message)
