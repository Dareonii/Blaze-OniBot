from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    websocket_url: str
    websocket_token: str | None
    websocket_room: str | None
    telegram_token: str | None
    telegram_chat_id: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            websocket_url=os.getenv(
                "BLAZE_DOUBLE_WS",
                "wss://api-gaming.blaze.bet.br/replication/?EIO=3&transport=websocket",
            ),
            websocket_token=os.getenv("BLAZE_DOUBLE_TOKEN"),
            websocket_room=os.getenv("BLAZE_DOUBLE_ROOM", "double_room_1"),
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )
