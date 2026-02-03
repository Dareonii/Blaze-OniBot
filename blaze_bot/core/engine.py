from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import StrategyBase


@dataclass
class PredictionState:
    prediction: Dict[str, Any]


class Engine:
    def __init__(self, strategy: StrategyBase, notifiers: Iterable[Any]) -> None:
        self.strategy = strategy
        self.notifiers = list(notifiers)
        self.history: List[Dict[str, Any]] = []
        self.stats = Stats()
        self.last_prediction: Optional[PredictionState] = None

    def process_result(self, result: Dict[str, Any]) -> None:
        self.history.append(result)
        for notifier in self.notifiers:
            if hasattr(notifier, "result"):
                notifier.result(result)

        if self.last_prediction is not None:
            win = self.strategy.validate(self.last_prediction.prediction, result)
            self.stats.register_result(win)
            for notifier in self.notifiers:
                if hasattr(notifier, "evaluation"):
                    notifier.evaluation(win, result, self.stats.winrate)
            for notifier in self.notifiers:
                if hasattr(notifier, "stats"):
                    notifier.stats(
                        self.stats.winrate,
                        {
                            "entries": self.stats.total_entries,
                            "wins": self.stats.wins,
                            "losses": self.stats.losses,
                        },
                    )

        self.strategy.analyze(self.history)
        prediction = self.strategy.predict(self.history)
        self.last_prediction = PredictionState(prediction=prediction)
        for notifier in self.notifiers:
            if hasattr(notifier, "prediction"):
                notifier.prediction(prediction)

    def snapshot_stats(self) -> Dict[str, Any]:
        return {
            "entries": self.stats.total_entries,
            "wins": self.stats.wins,
            "losses": self.stats.losses,
            "winrate": self.stats.winrate,
        }
