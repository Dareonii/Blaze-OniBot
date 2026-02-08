from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


class Strategy(StrategyBase):
    """Aposta na cor menos frequente em uma janela curta."""

    MARTINGALE = 1
    MARTINGALE_FACTOR = 1.1
    WINDOW = 12
    MIN_DIFF = 4

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        recent = [
            item.get("color")
            for item in history[-self.WINDOW :]
            if item.get("color") in {"red", "black"}
        ]
        counts = Counter(recent)
        red = counts.get("red", 0)
        black = counts.get("black", 0)
        diff = abs(red - black)
        target: Optional[str] = None
        if len(recent) >= self.WINDOW and diff >= self.MIN_DIFF:
            target = "red" if red < black else "black"
        return {
            "counts": dict(counts),
            "diff": diff,
            "target": target,
        }

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(history) < self.WINDOW:
            return None
        analysis = self.analyze(history)
        target = analysis["target"]
        if target is None:
            return None
        counts = analysis["counts"]
        reason = (
            f"Janela {self.WINDOW}: red={counts.get('red', 0)} "
            f"black={counts.get('black', 0)} (diff {analysis['diff']})"
        )
        return {"color": target, "reason": reason}

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        return prediction.get("color") == result.get("color")
