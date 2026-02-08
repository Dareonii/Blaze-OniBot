from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from blaze_bot.strategies.base import StrategyBase


class Strategy(StrategyBase):
    """Segue sequências curtas de vermelho/preto, ignorando branco."""

    MARTINGALE = 1
    MARTINGALE_FACTOR = 1.1
    MIN_STREAK = 3
    MAX_STREAK = 6

    def _current_streak(self, history: List[Dict[str, Any]]) -> Tuple[Optional[str], int]:
        if not history:
            return None, 0
        last_color = history[-1].get("color")
        if last_color not in {"red", "black"}:
            return None, 0
        length = 0
        for item in reversed(history):
            color = item.get("color")
            if color != last_color:
                break
            length += 1
        return last_color, length

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        color, length = self._current_streak(history)
        return {"streak_color": color, "streak_length": length}

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        color, length = self._current_streak(history)
        if color is None:
            return None
        if self.MIN_STREAK <= length <= self.MAX_STREAK:
            return {
                "color": color,
                "reason": f"Sequência ativa de {length} {color} (alvo {self.MIN_STREAK}-{self.MAX_STREAK})",
            }
        return None

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        return prediction.get("color") == result.get("color")
