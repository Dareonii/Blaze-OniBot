from __future__ import annotations

from typing import Any, Dict
import requests

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, game_label: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.game_label = game_label

    def send_message(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if response.ok:
            return

        details = ""
        try:
            payload = response.json()
            description = payload.get("description")
            error_code = payload.get("error_code")
            if description:
                details = f" (error_code={error_code}, description={description})"
        except ValueError:
            if response.text:
                details = f" (response={response.text})"

        raise requests.HTTPError(
            f"Telegram API request failed with status {response.status_code}{details}",
            response=response,
        )

    def prediction(self, prediction: Dict[str, Any]) -> None:
        color = prediction.get("color", "-")
        strategy = prediction.get("strategy") or "-"
        reason = prediction.get("reason")
        label, emoji = _format_color(color)
        lines = [
            "<b>⚠️ SINAL DETECTADO!",
            f"<b>🎲 Modo:</b> {self.game_label}",
            f"<b>🤖 Estratégia:</b> {strategy}",
            f"<b>🎯 Sinal:</b> {label} {emoji}".strip(),
        ]
        if reason:
            lines.append(f"<b>✳️ Motivo:</b> {reason}")
        self.send_message("\n".join(lines))

    def startup(self, strategies: list[str]) -> None:
        strategies_display = ", ".join(strategies) if strategies else "-"
        message = "\n".join(
            [
                "<b>🤖 Bot iniciado!</b>",
                f"<b>🎲 Modo:</b> {self.game_label}",
                f"<b>🧠 Estratégias ativas:</b> {strategies_display}",
            ]
        )
        self.send_message(message)

    def evaluation(
        self,
        win: bool,
        result: Dict[str, Any],
        winrate: float,
        stats: Dict[str, Any],
        *,
        strategy_name: str | None = None,
        min_winrate: float | None = None,
        max_winrate: float | None = None,
        bank_snapshot: Dict[str, float] | None = None,
    ) -> None:
        number = result.get("number", "-")
        _, emoji = _format_color(result.get("color", "-"))
        emoji = emoji or "-"
        status = (
            f"<b>✅️ WIN ({number}-{emoji})</b>"
            if win
            else f"<b>❌️ LOSS ({number}-{emoji})</b>"
        )
        strategy_label = strategy_name or "-"
        limits = ""
        if min_winrate is not None and max_winrate is not None:
            limits = f"({min_winrate:.2f}% - {max_winrate:.2f}%)"
        summary = (
            "📊 Entradas: {entries} | Wins: {wins} | Losses: {losses} | "
            "Winrate: {winrate:.2f}%{limits}".format(
                entries=stats["entries"],
                wins=stats["wins"],
                losses=stats["losses"],
                winrate=winrate,
                limits=limits,
            )
        )
        message_lines = [
            status,
            f"<b>🎲 Modo:</b> {self.game_label}",
            f"<b>🤖 Estratégia:</b> {strategy_label}",
            summary,
        ]
        if bank_snapshot:
            message_lines.extend(_format_bank_lines(bank_snapshot))
        self.send_message("\n".join(message_lines))


def _format_color(color: Any) -> tuple[str, str]:
    normalized = str(color).lower()
    mapping = {
        "red": ("<b>VERMELHO</b>", "🔴"),
        "black": ("<b>PRETO</b>", "⚫️"),
        "white": ("<b>BRANCO</b>", "⚪️"),
    }
    return mapping.get(normalized, (str(color).upper(), ""))


def _format_bank_lines(bank_snapshot: Dict[str, float]) -> list[str]:
    lines = ["<b>💰 BANCA(s):</b>"]
    for name, value in bank_snapshot.items():
        formatted = _format_currency(value)
        lines.append(f"<b> 🪙 {name}:</b> {formatted}")
    return lines


def _format_currency(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
