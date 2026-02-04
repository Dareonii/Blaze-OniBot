from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

import websockets

logger = logging.getLogger(__name__)


class BlazeDoubleWebSocket:
    def __init__(self, url: str) -> None:
        self.url = url
        self._last_status: str | None = None

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        backoff = 1
        while True:
            try:
                logger.info("Iniciando conexão com o WebSocket: %s", self.url)
                async with websockets.connect(self.url, ping_interval=20, ping_timeout=20) as socket:
                    logger.info("Conexão WebSocket estabelecida com sucesso.")
                    backoff = 1
                    async for message in socket:
                        parsed = self._parse_message(message)
                        if parsed:
                            yield parsed
                    logger.warning("Conexão WebSocket encerrada.")
            except (OSError, websockets.WebSocketException) as exc:
                logger.warning(
                    "Falha ao conectar/manter o WebSocket. Nova tentativa em %ss. Motivo: %s",
                    backoff,
                    exc,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    def _parse_message(self, message: str) -> Dict[str, Any] | None:
        if message.startswith("42"):
            message = message[2:]
        elif message in {"2", "3"}:
            logger.debug("Ping/Pong do WebSocket recebido: %s", message)
            return None
        elif message:
            logger.debug("Mensagem WebSocket não processada: %s", message)
            return None
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return None

        data: Any
        if isinstance(payload, list) and len(payload) >= 2 and payload[0] == "data":
            data = payload[1]
        else:
            data = payload.get("data") if isinstance(payload, dict) else None

        if isinstance(data, dict) and isinstance(data.get("payload"), dict):
            data = data["payload"]

        if isinstance(data, dict):
            status = data.get("status")
            if isinstance(status, str) and status != self._last_status:
                logger.info("Status do double: %s", status)
                if status == "waiting":
                    logger.info("Roleta aguardando próxima rodada (sem número ainda).")
                self._last_status = status
            color = data.get("color") or data.get("colour")
            number = data.get("roll") or data.get("number")
            timestamp = data.get("created_at") or data.get("timestamp")
        else:
            color = payload.get("color") if isinstance(payload, dict) else None
            number = payload.get("roll") if isinstance(payload, dict) else None
            timestamp = payload.get("created_at") if isinstance(payload, dict) else None

        if color is None or number is None:
            if isinstance(data, dict) and data.get("status") == "waiting":
                logger.info("Roleta aguardando próxima rodada (sem número ainda).")
            return None

        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        return {"timestamp": timestamp, "number": int(number), "color": self._normalize_color(color)}

    def _normalize_color(self, color: Any) -> str:
        if isinstance(color, str):
            return color
        mapping = {0: "white", 1: "red", 2: "black"}
        return mapping.get(int(color), str(color))
