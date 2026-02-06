from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


class Strategy(StrategyBase):
    """Gera sinal quando 14+ das últimas 20 cores forem iguais (aposta simples)."""

    MARTINGALE = 0

    def __init__(self) -> None:
        self._active_color: Optional[str] = None
        self._loss_streak = 0
        self._last_history_len = 0
        self._stopped_at_len: Optional[int] = None

    def _update_state(self, history: List[Dict[str, Any]]) -> None:
        if not history:
            self._last_history_len = 0
            return
        new_results = history[self._last_history_len :]
        current_len = self._last_history_len
        for result in new_results:
            current_len += 1
            if not self._active_color:
                continue
            color = result.get("color")
            if color == self._active_color:
                self._loss_streak = 0
                continue
            self._loss_streak += 1
            if self._loss_streak >= 3:
                self._active_color = None
                self._loss_streak = 0
                self._stopped_at_len = current_len
        self._last_history_len = len(history)

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._update_state(history)
        colors = [item.get("color") for item in history[-20:] if item.get("color")]
        counts = Counter(colors)
        white_count = counts.get("white", 0)
        threshold = 13 if white_count > 0 else 14
        color_counts = {color: counts.get(color, 0) for color in ("red", "black")}
        dominant_color = None
        dominant_count = 0
        for color, count in color_counts.items():
            if count >= threshold and count > dominant_count:
                dominant_color = color
                dominant_count = count
        return {
            "dominant_color": dominant_color,
            "dominant_count": dominant_count,
            "counts": dict(counts),
            "threshold": threshold,
        }

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < 20:
            return None

        analysis = self.analyze(history)

        dominant = analysis["dominant_color"]
        threshold = analysis["threshold"]

        if self._active_color is None:
            if dominant is None or self._stopped_at_len == len(history):
                return None
            self._active_color = dominant
            self._loss_streak = 0
            self._stopped_at_len = None

        dominant_count = analysis["counts"].get(self._active_color, 0)
        reason = f"{dominant_count}/20 COR DOMINANTE (MIN {threshold})"

        return {"color": self._active_color, "reason": reason}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        result_color = result.get("color")
        return prediction.get("color") == result_color
