from __future__ import annotations

from typing import Any, Dict, List, Optional
from blaze_bot.strategies.base import StrategyBase
from collections import Counter

class Strategy(StrategyBase):
    """Sinaliza branco quando uma cor domina 14/20 resultados recentes."""

    MARTINGALE = 13
    MARTINGALE_FACTOR = 1.1

    def __init__(self) -> None:
        self._active = False
        self._losses = 0
        self._stopped_at_len: Optional[int] = None
        self._pending_stop_len = False

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self._pending_stop_len:
            self._stopped_at_len = len(history)
            self._pending_stop_len = False
        colors = [item.get("color") for item in history[-20:] if item.get("color")]
        counts = Counter(colors)
        dominant_count = max(counts.values()) if counts else 0
        return {"counts": dict(counts), "dominant_count": dominant_count}

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < 20:
            return None

        analysis = self.analyze(history)

        if self._active:
            return None

        if analysis["dominant_count"] < 14 or self._stopped_at_len == len(history):
            return None
        self._active = True
        self._losses = 0
        self._stopped_at_len = None

        return {
            "color": "white",
            "win_weight": 14,
            "loss_weight": 1,
            "entry_weight": 1,
            "count_each_roll": True,
        }

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        if result.get("color") == "white":
            self._active = False
            self._losses = 0
            self._pending_stop_len = True
            return True

        if self._active:
            self._losses += 1
            if self._losses >= 14:
                self._active = False
                self._losses = 0
                self._pending_stop_len = True
        return False
