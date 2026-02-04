from __future__ import annotations

from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


STRATEGY_NAME = "Flow"


class Strategy(StrategyBase):
    """Repete a última cor sorteada que não seja branco."""

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        last_color = None
        for entry in reversed(history):
            color = entry.get("color")
            if color and str(color).lower() != "white":
                last_color = color
                break
        return {"last_non_white": last_color}

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        analysis = self.analyze(history)
        last_color = analysis.get("last_non_white")
        if not last_color:
            return None
        return {"color": last_color}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        return prediction.get("color") == result.get("color")
