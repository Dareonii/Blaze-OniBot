from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    websocket_url: str
    websocket_token: str | None
    websocket_room: str | None
    websocket_result_timeout: float
    websocket_reconnect_backoff_initial: float
    websocket_reconnect_backoff_max: float
    history_url: str | None
    history_limit: int
    history_timeout: float
    preload_history: bool
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
            websocket_result_timeout=float(os.getenv("BLAZE_DOUBLE_RESULT_TIMEOUT", "120")),
            websocket_reconnect_backoff_initial=float(
                os.getenv("BLAZE_DOUBLE_RECONNECT_BACKOFF_INITIAL", "1")
            ),
            websocket_reconnect_backoff_max=float(
                os.getenv("BLAZE_DOUBLE_RECONNECT_BACKOFF_MAX", "10")
            ),
            history_url=os.getenv(
                "BLAZE_DOUBLE_HISTORY_URL",
                "https://api-gaming.blaze.bet.br/api/roulette_games/recent",
            ),
            history_limit=int(os.getenv("BLAZE_DOUBLE_HISTORY_LIMIT", "200")),
            history_timeout=float(os.getenv("BLAZE_DOUBLE_HISTORY_TIMEOUT", "10")),
            preload_history=_parse_bool(os.getenv("BLAZE_DOUBLE_PRELOAD_HISTORY", "true")),
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", "8214223602:AAG9Ut7QVpTX8aZkS316PcELX94Ci5WaYFM"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "-5138181857"),
        )


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "sim", "s"}
