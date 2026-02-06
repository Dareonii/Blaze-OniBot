from __future__ import annotations

from typing import Any, Dict


class TerminalNotifier:
    def result(self, result: Dict[str, Any]) -> None:
        color = result.get("color", "-")
        label, emoji = _format_color(color)
        print(f"[DOUBLE] {result['number']} {emoji} ({label})")

    def prediction(self, prediction: Dict[str, Any]) -> None:
        label, emoji = _format_prediction(prediction)
        strategy = prediction.get("strategy")
        strategy_label = f"({strategy})" if strategy else ""
        print(f"[STRATEGY] ({label}) {emoji} {strategy_label}")

    def evaluation(
        self,
        win: bool,
        result: Dict[str, Any] | None = None,
        winrate: float | None = None,
        stats: Dict[str, Any] | None = None,
        *,
        strategy_name: str | None = None,
        min_winrate: float | None = None,
        max_winrate: float | None = None,
        bank_snapshot: Dict[str, float] | None = None,
    ) -> None:
        number = "-"
        emoji = ""
        if result:
            number = result.get("number", "-")
            _, emoji = _format_color(result.get("color", "-"))
        emoji = emoji or "-"
        label = f"✅️ WIN ({number}-{emoji})" if win else f"❌️ LOSS ({number}-{emoji})"
        suffix = f"({strategy_name})" if strategy_name else ""
        stats_summary = ""
        if stats and winrate is not None:
            limits = ""
            if min_winrate is not None and max_winrate is not None:
                limits = f" (mín: {min_winrate:.2f}% | máx: {max_winrate:.2f}%)"
            stats_summary = (
                " Entradas: {entries} | Wins: {wins} | Loss: {losses} | Winrate: {winrate:.2f}%{limits}".format(
                    entries=_format_stat(stats["entries"]),
                    wins=_format_stat(stats["wins"]),
                    losses=_format_stat(stats["losses"]),
                    winrate=winrate,
                    limits=limits,
                )
            )
        print(f"[RESULT] {label}{suffix}{stats_summary}")
        if bank_snapshot:
            print(_format_bank_lines(bank_snapshot))

    def stats(
        self,
        winrate: float,
        stats: Dict[str, Any],
        *,
        strategy_name: str | None = None,
        min_winrate: float | None = None,
        max_winrate: float | None = None,
    ) -> None:
        prefix = f"[{strategy_name}]" if strategy_name else "[STATS]"
        limits = ""
        if min_winrate is not None and max_winrate is not None and strategy_name:
            limits = f" | Min: {min_winrate:.2f}% | Max: {max_winrate:.2f}%"
        print(
            "{prefix} Entradas: {entries} | Wins: {wins} | Loss: {losses} | Winrate: {winrate:.2f}%{limits}".format(
                prefix=prefix,
                entries=_format_stat(stats["entries"]),
                wins=_format_stat(stats["wins"]),
                losses=_format_stat(stats["losses"]),
                winrate=winrate,
                limits=limits,
            )
        )

    def warning(self, message: str) -> None:
        print(f"[WARN] {message}")


def _format_color(color: Any) -> tuple[str, str]:
    normalized = str(color).lower()
    mapping = {
        "red": ("RED", "🔴"),
        "black": ("BLACK", "⚫"),
        "white": ("WHITE", "⚪"),
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


def _format_bank_lines(bank_snapshot: Dict[str, float]) -> str:
    lines = ["💰 BANCA(s):"]
    for name, value in bank_snapshot.items():
        lines.append(f" 🪙 {name}: {_format_currency(value)}")
    return "\n".join(lines)


def _format_currency(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
