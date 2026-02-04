from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import StrategyBase


@dataclass
class PredictionState:
    prediction: Dict[str, Any]
    strategy_name: str


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
            self.last_prediction = None

        self.strategy.analyze(self.history)
        prediction = self.strategy.predict(self.history)
        if prediction is None:
            return
        strategy_name = self.strategy.__class__.__name__
        self.last_prediction = PredictionState(prediction=prediction, strategy_name=strategy_name)
        prediction_payload = {**prediction, "strategy": strategy_name}
        for notifier in self.notifiers:
            if hasattr(notifier, "prediction"):
                notifier.prediction(prediction_payload)

    def snapshot_stats(self) -> Dict[str, Any]:
        return {
            "entries": self.stats.total_entries,
            "wins": self.stats.wins,
            "losses": self.stats.losses,
            "winrate": self.stats.winrate,
        }
