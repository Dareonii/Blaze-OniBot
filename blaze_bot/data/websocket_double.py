from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

import websockets

logger = logging.getLogger(__name__)


class BlazeDoubleWebSocket:
    def __init__(
        self,
        url: str,
        *,
        token: str | None = None,
        room: str | None = "double_room_1",
        namespace: str = "",
    ) -> None:
        self.url = url
        self.token = token
        self.room = room
        self._last_status: str | None = None
        self._last_result_signature: tuple[Any, ...] | None = None
        self._namespace = namespace

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        backoff = 1
        while True:
            try:
                logger.info("Iniciando conexão com o WebSocket: %s", self.url)
                async with websockets.connect(self.url, ping_interval=None, ping_timeout=None) as socket:
                    logger.info("Conexão WebSocket estabelecida com sucesso.")
                    await self._send_connect(socket)
                    backoff = 1
                    async for message in socket:
                        if await self._handle_control_message(socket, message):
                            continue
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

    async def _send_connect(self, socket: websockets.WebSocketClientProtocol) -> None:
        """Envia o comando de conexão do Socket.IO (Engine.IO v3)."""
        if self._namespace:
            await socket.send(f"40{self._namespace}")
        else:
            await socket.send("40")

    async def _handle_control_message(
        self, socket: websockets.WebSocketClientProtocol, message: str
    ) -> bool:
        if message.startswith("0"):
            try:
                payload = json.loads(message[1:]) if len(message) > 1 else {}
            except json.JSONDecodeError:
                payload = {}
            ping_interval = payload.get("pingInterval")
            ping_timeout = payload.get("pingTimeout")
            logger.info(
                "Handshake Engine.IO recebido (pingInterval=%s, pingTimeout=%s).",
                ping_interval,
                ping_timeout,
            )
            await self._send_connect(socket)
            await self._send_initial_messages(socket)
            return True
        if message == "2":
            logger.debug("Ping Engine.IO recebido, enviando pong.")
            await socket.send("3")
            return True
        if message in {"3", "40", f"40{self._namespace}"}:
            logger.debug("Mensagem Engine.IO ignorada: %s", message)
            return True
        return False

    async def _send_initial_messages(self, socket: websockets.WebSocketClientProtocol) -> None:
        if self.token:
            await self._send_cmd(socket, {"id": "authenticate", "payload": {"token": self.token}})
            logger.info("Comando de autenticação enviado.")
        if self.room:
            await self._send_cmd(socket, {"id": "subscribe", "payload": {"room": self.room}})
            logger.info("Inscrição enviada para a sala %s.", self.room)

    async def _send_cmd(
        self, socket: websockets.WebSocketClientProtocol, payload: Dict[str, Any]
    ) -> None:
        message = json.dumps(["cmd", payload], separators=(",", ":"))
        if self._namespace:
            namespace = self._namespace if self._namespace.startswith("/") else f"/{self._namespace}"
            await socket.send(f"42{namespace},{message}")
        else:
            await socket.send(f"42{message}")

    def _parse_message(self, message: str) -> Dict[str, Any] | None:
        if message.startswith("42"):
            message = message[2:]
            if message.startswith("/"):
                _, _, payload = message.partition(",")
                message = payload
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

        status = data.get("status") if isinstance(data, dict) else None
        if isinstance(status, str) and status != self._last_status:
            logger.info("Status do double: %s", status)
            if status == "waiting":
                logger.info("Roleta aguardando próxima rodada (sem número ainda).")
            self._last_status = status
        if status == "waiting":
            self._last_status = "waiting"
            return None

        if isinstance(data, dict):
            color = data.get("color") or data.get("colour")
            number = data.get("roll") or data.get("number")
            timestamp = data.get("created_at") or data.get("timestamp")
        else:
            color = payload.get("color") if isinstance(payload, dict) else None
            number = payload.get("roll") if isinstance(payload, dict) else None
            timestamp = payload.get("created_at") if isinstance(payload, dict) else None

        if color is None or number is None:
            return None

        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        normalized_color = self._normalize_color(color)
        signature = (int(number), normalized_color, timestamp)
        if self._last_result_signature == signature:
            return None
        self._last_result_signature = signature

        return {"timestamp": timestamp, "number": int(number), "color": normalized_color}

    def _normalize_color(self, color: Any) -> str:
        if isinstance(color, str):
            return color
        mapping = {0: "white", 1: "red", 2: "black"}
        return mapping.get(int(color), str(color))
