from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


STRATEGY_NAME = "supremacia"


class Strategy(StrategyBase):
    """Gera sinal quando 14+ das últimas 20 cores forem iguais."""

    MARTINGALE = 1

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

        counts = analysis["counts"]
        adjusted = analysis["adjusted_counts"]
        dominant = analysis["dominant_color"]

        dominant_color = max(adjusted, key=adjusted.get)
        dominant_count = adjusted[dominant_color]

        print(
            f"[SUPREMACIA] Dominância: {dominant_color.upper()} "
            f"({dominant_count}/20) | "
            f"Red: {counts.get('red', 0)} | "
            f"Black: {counts.get('black', 0)} | "
            f"White: {counts.get('white', 0)}"
        )

        if dominant is None:
            return None

        return {"color": dominant}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        result_color = result.get("color")
        if result_color == "white":
            return True
        return prediction.get("color") == result_color
