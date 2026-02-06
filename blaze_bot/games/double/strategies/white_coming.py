from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


class Strategy(StrategyBase):
    """Sinaliza branco quando uma cor domina 14/20 resultados recentes."""

    def __init__(self) -> None:
        self._active = False
        self._losses = 0
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
            if not self._active:
                continue
            color = result.get("color")
            if color == "white":
                self._active = False
                self._losses = 0
                self._stopped_at_len = current_len
                continue
            self._losses += 1
            if self._losses >= 14:
                self._active = False
                self._losses = 0
                self._stopped_at_len = current_len
        self._last_history_len = len(history)

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._update_state(history)
        colors = [item.get("color") for item in history[-20:] if item.get("color")]
        counts = Counter(colors)
        dominant_count = max(counts.values()) if counts else 0
        return {"counts": dict(counts), "dominant_count": dominant_count}

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < 20:
            return None

        analysis = self.analyze(history)

        if not self._active:
            if analysis["dominant_count"] < 14 or self._stopped_at_len == len(history):
                return None
            self._active = True
            self._losses = 0
            self._stopped_at_len = None

        return {"color": "white", "win_weight": 14, "loss_weight": 1}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        return result.get("color") == "white"
