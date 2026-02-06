from __future__ import annotations
from typing import Any, Dict, List
from blaze_bot.strategies.base import StrategyBase

STRATEGY_NAME = "dummy"

class Strategy(StrategyBase):
    """Alterna entre vermelho e preto ignorando o branco."""

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        last_color = history[-1]["color"] if history else "red"
        next_color = "black" if last_color == "red" else "red"
        return {"next_color": next_color}

    def predict(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis = self.analyze(history)
        return {"color": analysis["next_color"]}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        return prediction.get("color") == result.get("color")
