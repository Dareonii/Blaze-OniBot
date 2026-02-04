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
        dominant_color = None
        for color, count in counts.items():
            if count >= 14:
                dominant_color = color
                break
        return {"dominant_color": dominant_color, "counts": dict(counts)}

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
