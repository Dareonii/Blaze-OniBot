from __future__ import annotations

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, game_label: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.game_label = game_label

    def send_message(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            response = requests.post(
                url,
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.warning("Falha ao enviar mensagem para o Telegram: %s", exc)
            return

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

        logger.warning(
            "Telegram API retornou status %s%s",
            response.status_code,
            details,
        )

    def prediction(self, prediction: Dict[str, Any]) -> None:
        strategy = prediction.get("strategy") or "-"
        label, emoji = _format_prediction(prediction)
        lines = [
            "⚠️ SINAL DETECTADO",
            f"🎲 Modo: {self.game_label}",
            f"🤖 Estratégia: {strategy}",
            f"🎯 Sinal: {label} {emoji}".strip(),
        ]
        self.send_message("\n".join(lines))

    def startup(self, strategies: list[str]) -> None:
        strategies_display = ", ".join(strategies) if strategies else "-"
        message = "\n".join(
            [
                "🤖 Bot iniciado",
                f"🎲 Modo: {self.game_label}",
                f"🧠 Estratégias ativas: {strategies_display}",
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
        status = f"✅️ WIN ({number}-{emoji})" if win else f"❌️ LOSS ({number}-{emoji})"
        strategy_label = strategy_name or "-"
        summary = (
            "📊 Entradas: {entries} | Wins: {wins} | Losses: {losses} | "
            "Winrate: {winrate:.2f}%".format(
                entries=_format_stat(stats["entries"]),
                wins=_format_stat(stats["wins"]),
                losses=_format_stat(stats["losses"]),
                winrate=winrate,
            )
        )
        message_lines = [
            status,
            f"🎲 Modo: {self.game_label}",
            f"🤖 Estratégia: {strategy_label}",
            summary,
        ]
        if bank_snapshot:
            message_lines.extend(_format_bank_lines(bank_snapshot, strategy_label))
        self.send_message("\n".join(message_lines))


def _format_color(color: Any) -> tuple[str, str]:
    normalized = str(color).lower()
    mapping = {
        "red": ("VERMELHO", "🔴"),
        "black": ("PRETO", "⚫️"),
        "white": ("BRANCO", "⚪️"),
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
            labels.append(f"{label} {percent}".strip())
            if emoji:
                emojis.append(emoji)
        return " + ".join(labels), "".join(emojis)
    color = prediction.get("color", "-")
    return _format_color(color)


def _format_bank_lines(bank_snapshot: Dict[str, Any], strategy_name: str) -> list[str]:
    strategy_bank = _pick_strategy_bank(bank_snapshot, strategy_name)
    if strategy_bank is None:
        return []

    base_value, martingale_value, _enabled = _split_bank_values(strategy_bank)
    base_min = _get_stat_value(strategy_bank, "base_min")
    base_max = _get_stat_value(strategy_bank, "base_max")
    martingale_min = _get_stat_value(strategy_bank, "martingale_min")
    martingale_max = _get_stat_value(strategy_bank, "martingale_max")

    base_range = _format_range(base_min, base_max)
    mg_range = _format_range(martingale_min, martingale_max)

    return [
        f"💰 Banca: {_format_currency(base_value)}{base_range}",
        f"📈 Martingale: {_format_currency(martingale_value)}{mg_range}",
    ]


def _pick_strategy_bank(
    bank_snapshot: Dict[str, Any], strategy_name: str
) -> Dict[str, Any] | None:
    if not isinstance(bank_snapshot, dict) or not bank_snapshot:
        return None
    if strategy_name in bank_snapshot and isinstance(bank_snapshot[strategy_name], dict):
        return bank_snapshot[strategy_name]
    first = next(iter(bank_snapshot.values()))
    if isinstance(first, dict):
        return first
    return None


def _format_range(min_value: float | None, max_value: float | None) -> str:
    if min_value is None or max_value is None:
        return ""
    return f" ({_format_currency(min_value)}-{_format_currency(max_value)})"


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


def _get_stat_value(value: Any, key: str) -> float | None:
    if not isinstance(value, dict):
        return None
    data = value.get(key)
    if data is None:
        return None
    try:
        return float(data)
    except (TypeError, ValueError):
        return None
