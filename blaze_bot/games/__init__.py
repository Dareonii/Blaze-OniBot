from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from blaze_bot.config.settings import Settings
from blaze_bot.data.websocket_double import BlazeDoubleWebSocket


@dataclass(frozen=True)
class GameConfig:
    key: str
    label: str
    strategy_package: str
    socket_builder: Callable[[Settings], Any]


def _build_double_socket(settings: Settings) -> BlazeDoubleWebSocket:
    return BlazeDoubleWebSocket(
        settings.websocket_url,
        token=settings.websocket_token,
        room=settings.websocket_room,
        reconnect_backoff_initial=settings.websocket_reconnect_backoff_initial,
        reconnect_backoff_max=settings.websocket_reconnect_backoff_max,
    )


def available_games() -> Dict[str, GameConfig]:
    return {
        "double": GameConfig(
            key="double",
            label="Double",
            strategy_package="blaze_bot.games.double.strategies",
            socket_builder=_build_double_socket,
        )
    }


def default_game_key() -> str:
    games = available_games()
    if not games:
        raise ValueError("Nenhum jogo disponível.")
    return next(iter(games.keys()))
