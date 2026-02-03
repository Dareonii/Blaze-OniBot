from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    websocket_url: str
    telegram_token: str | None
    telegram_chat_id: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            websocket_url=os.getenv("BLAZE_DOUBLE_WS", "wss://api-v2.blaze.com/roulette/"),
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )
