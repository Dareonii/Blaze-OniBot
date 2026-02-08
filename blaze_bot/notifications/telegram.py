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
        strategy = prediction.get("strategy") or "-"
        reason = prediction.get("reason")
        label, emoji = _format_prediction(prediction)
        lines = [
            "<b>⚠️ SINAL DETECTADO!</b>",
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
        bank_snapshot: Dict[str, Any] | None = None,
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
                entries=_format_stat(stats["entries"]),
                wins=_format_stat(stats["wins"]),
                losses=_format_stat(stats["losses"]),
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


def _format_prediction(prediction: Dict[str, Any]) -> tuple[str, str]:
    bet_split = prediction.get("bet_split")
    if bet_split:
        labels = []
        emojis = []
        for item in bet_split:
            label, emoji = _format_color(item.get("color", "-"))
            percent = _format_percent(item.get("weight"))
            if percent:
                labels.append(f"{label} {percent}")
            else:
                labels.append(label)
            if emoji:
                emojis.append(emoji)
        return " + ".join(labels), "".join(emojis)
    color = prediction.get("color", "-")
    return _format_color(color)


def _format_bank_lines(bank_snapshot: Dict[str, Any]) -> list[str]:
    lines = ["<b>💰 BANCA:</b>"]
    for name, value in bank_snapshot.items():
        base_value, martingale_value, martingale_enabled = _split_bank_values(value)
        formatted = _format_currency(base_value)
        if martingale_enabled:
            formatted = f"{formatted} ({_format_currency(martingale_value)})"
        lines.append(f"<b> 🪙 {name}:</b> {formatted}")
    return lines


def _format_currency(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _split_bank_values(value: Any) -> tuple[float, float, bool]:
    if isinstance(value, dict):
        base = value.get("base", 0.0)
        martingale = value.get("martingale", base)
        enabled = bool(value.get("martingale_enabled"))
        return float(base), float(martingale), enabled
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0, 0.0, False
    return numeric, numeric, False


def _format_percent(weight: Any) -> str:
    if weight is None:
        return ""
    try:
        percent = float(weight) * 100
    except (TypeError, ValueError):
        return ""
    if percent.is_integer():
        return f"{int(percent)}%"
    return f"{percent:.1f}%"


def _format_stat(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}"
