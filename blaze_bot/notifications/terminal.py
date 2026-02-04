from __future__ import annotations

from typing import Any, Dict


class TerminalNotifier:
    def result(self, result: Dict[str, Any]) -> None:
        color = result.get("color", "-")
        label, emoji = _format_color(color)
        print(f"[DOUBLE] {result['number']} {emoji} ({label})")

    def prediction(self, prediction: Dict[str, Any]) -> None:
        color = prediction.get("color", "-")
        label, emoji = _format_color(color)
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
    ) -> None:
        label = "WIN ✅" if win else "LOSS ❌"
        suffix = f"({strategy_name})" if strategy_name else ""
        stats_summary = ""
        if stats and winrate is not None:
            limits = ""
            if min_winrate is not None and max_winrate is not None:
                limits = f" (mín: {min_winrate:.2f}% | máx: {max_winrate:.2f}%)"
            stats_summary = (
                " Entradas: {entries} | Wins: {wins} | Loss: {losses} | Winrate: {winrate:.2f}%{limits}".format(
                    entries=stats["entries"],
                    wins=stats["wins"],
                    losses=stats["losses"],
                    winrate=winrate,
                    limits=limits,
                )
            )
        print(f"[RESULT] {label}{suffix}{stats_summary}")

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
                entries=stats["entries"],
                wins=stats["wins"],
                losses=stats["losses"],
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
