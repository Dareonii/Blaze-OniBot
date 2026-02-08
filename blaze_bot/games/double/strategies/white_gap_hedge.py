from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


class Strategy(StrategyBase):
    """Hedge entre cor dominante e branco após longos gaps sem branco."""

    MARTINGALE = 0
    GAP_THRESHOLD = 18
    WINDOW = 10
    DOMINANCE = 7

    def _rolls_since_white(self, history: List[Dict[str, Any]]) -> int:
        gap = 0
        for item in reversed(history):
            if item.get("color") == "white":
                break
            gap += 1
        return gap

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        gap = self._rolls_since_white(history)
        recent = [
            item.get("color")
            for item in history[-self.WINDOW :]
            if item.get("color") in {"red", "black"}
        ]
        counts = Counter(recent)
        dominant_color = None
        dominant_count = 0
        for color in ("red", "black"):
            count = counts.get(color, 0)
            if count > dominant_count:
                dominant_color = color
                dominant_count = count
        return {
            "gap": gap,
            "counts": dict(counts),
            "dominant_color": dominant_color,
            "dominant_count": dominant_count,
        }

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < self.WINDOW:
            return None
        analysis = self.analyze(history)
        if analysis["gap"] < self.GAP_THRESHOLD:
            return None
        dominant_color = analysis["dominant_color"]
        if dominant_color is None or analysis["dominant_count"] < self.DOMINANCE:
            return None
        reason = (
            f"Gap branco {analysis['gap']} + dominante {dominant_color} "
            f"({analysis['dominant_count']}/{self.WINDOW})"
        )
        return {
            "bet_split": [
                {"color": dominant_color, "weight": 0.85},
                {"color": "white", "weight": 0.15},
            ],
            "reason": reason,
        }

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        result_color = result.get("color")
        bet_split = prediction.get("bet_split")
        if bet_split:
            return any(item.get("color") == result_color for item in bet_split)
        return prediction.get("color") == result_color
