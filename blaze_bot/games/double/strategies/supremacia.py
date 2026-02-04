from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


STRATEGY_NAME = "supremacia"


class Strategy(StrategyBase):
    """Gera sinal quando 14+ das últimas 20 cores forem iguais."""

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        colors = [item.get("color") for item in history[-20:] if item.get("color")]
        counts = Counter(colors)
        white_count = counts.get("white", 0)
        adjusted_counts = {
            "red": counts.get("red", 0) + white_count,
            "black": counts.get("black", 0) + white_count,
        }
        dominant_color = None
        dominant_count = 0
        for color in ("red", "black"):
            count = adjusted_counts.get(color, 0)
            if count >= 14 and count > dominant_count:
                dominant_color = color
                dominant_count = count
        return {
            "dominant_color": dominant_color,
            "counts": dict(counts),
            "adjusted_counts": adjusted_counts,
        }

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < 20:
            return None
        analysis = self.analyze(history)
        dominant = analysis.get("dominant_color")
        if dominant is None:
            return None
        return {"color": dominant}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        return prediction.get("color") == result.get("color")
