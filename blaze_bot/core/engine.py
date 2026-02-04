from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import MultiStrategy, StrategyBase


@dataclass
class PredictionState:
    prediction: Dict[str, Any]
    strategy_name: str
    strategy: StrategyBase


class Engine:
    def __init__(self, strategy: StrategyBase, notifiers: Iterable[Any]) -> None:
        self.strategy = strategy
        self.notifiers = list(notifiers)
        self.history: List[Dict[str, Any]] = []
        self.stats = Stats()
        self.strategy_stats: Dict[str, Stats] = {}
        self.last_predictions: List[PredictionState] = []

    def _stats_for_strategy(self, strategy_name: str) -> Stats:
        stats = self.strategy_stats.get(strategy_name)
        if stats is None:
            stats = Stats()
            self.strategy_stats[strategy_name] = stats
        return stats

    @staticmethod
    def _normalize_predictions(
        prediction: Dict[str, Any] | Sequence[Dict[str, Any]] | None,
    ) -> List[Dict[str, Any]]:
        if prediction is None:
            return []
        if isinstance(prediction, dict):
            return [prediction]
        return [item for item in prediction if item]

    def process_result(self, result: Dict[str, Any]) -> None:
        self.history.append(result)
        for notifier in self.notifiers:
            if hasattr(notifier, "result"):
                notifier.result(result)

        if self.last_predictions:
            for prediction_state in self.last_predictions:
                strategy_name = prediction_state.strategy_name
                win = prediction_state.strategy.validate(prediction_state.prediction, result)
                self.stats.register_result(win)
                strategy_stats = self._stats_for_strategy(strategy_name)
                strategy_stats.register_result(win)
                for notifier in self.notifiers:
                    if hasattr(notifier, "evaluation"):
                        notifier.evaluation(
                            win,
                            result,
                            strategy_stats.winrate,
                            strategy_name=strategy_name,
                        )
                for notifier in self.notifiers:
                    if hasattr(notifier, "stats"):
                        notifier.stats(
                            strategy_stats.winrate,
                            {
                                "entries": strategy_stats.total_entries,
                                "wins": strategy_stats.wins,
                                "losses": strategy_stats.losses,
                            },
                            strategy_name=strategy_name,
                        )
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
            self.last_predictions = []

        self.strategy.analyze(self.history)
        if isinstance(self.strategy, MultiStrategy):
            predictions = self.strategy.predictions_with_strategies(self.history)
            if not predictions:
                return
            for strategy, prediction_item in predictions:
                strategy_name = strategy.strategy_name()
                prediction_state = PredictionState(
                    prediction=prediction_item,
                    strategy_name=strategy_name,
                    strategy=strategy,
                )
                self.last_predictions.append(prediction_state)
                prediction_payload = {**prediction_item, "strategy": strategy_name}
                for notifier in self.notifiers:
                    if hasattr(notifier, "prediction"):
                        notifier.prediction(prediction_payload)
            return

        prediction = self.strategy.predict(self.history)
        normalized_predictions = self._normalize_predictions(prediction)
        if not normalized_predictions:
            return
        for prediction_item in normalized_predictions:
            strategy_name = self.strategy.strategy_name()
            prediction_state = PredictionState(
                prediction=prediction_item,
                strategy_name=strategy_name,
                strategy=self.strategy,
            )
            self.last_predictions.append(prediction_state)
            prediction_payload = {**prediction_item, "strategy": strategy_name}
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
