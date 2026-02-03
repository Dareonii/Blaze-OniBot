from __future__ import annotations

from typing import Any, Dict


class TerminalNotifier:
    def result(self, result: Dict[str, Any]) -> None:
        print(f"[DOUBLE] Resultado: {result['number']} ({result['color']})")

    def prediction(self, prediction: Dict[str, Any]) -> None:
        color = prediction.get("color", "-")
        print(f"[STRATEGY] Predição: {color}")

    def evaluation(
        self, win: bool, result: Dict[str, Any] | None = None, winrate: float | None = None
    ) -> None:
        label = "WIN" if win else "LOSS"
        print(f"[RESULT] {label}")

    def stats(self, winrate: float, stats: Dict[str, Any]) -> None:
        print(
            "[STATS] Entradas: {entries} | Wins: {wins} | Losses: {losses} | Winrate: {winrate:.2f}%".format(
                entries=stats["entries"],
                wins=stats["wins"],
                losses=stats["losses"],
                winrate=winrate,
            )
        )
