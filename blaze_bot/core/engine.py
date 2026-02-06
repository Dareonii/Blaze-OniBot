from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from blaze_bot.core.bank import BankManager
from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import MultiStrategy, StrategyBase


@dataclass
class PredictionState:
    prediction: Dict[str, Any]
    strategy_name: str
    strategy: StrategyBase
    remaining_martingale: int = 0
    counted: bool = False


class Engine:
    def __init__(
        self,
        strategy: StrategyBase,
        notifiers: Iterable[Any],
        bank_manager: BankManager | None = None,
    ) -> None:
        self.strategy = strategy
        self.notifiers = list(notifiers)
        self.history: List[Dict[str, Any]] = []
        self.stats = Stats()
        self.strategy_stats: Dict[str, Stats] = {}
        self.last_predictions: List[PredictionState] = []
        self.bank_manager = bank_manager

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

    @staticmethod
    def _match_bet_split(
        bet_split: Sequence[Dict[str, Any]], result: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        result_color = result.get("color")
        for item in bet_split:
            if item.get("color") == result_color:
                return item
        return None

    def process_result(self, result: Dict[str, Any]) -> None:
        self.history.append(result)
        for notifier in self.notifiers:
            if hasattr(notifier, "result"):
                notifier.result(result)

        if self.last_predictions:
            pending_predictions: List[PredictionState] = []
            registered_outcome = False
            for prediction_state in self.last_predictions:
                strategy_name = prediction_state.strategy_name
                prediction = prediction_state.prediction
                bet_split = prediction.get("bet_split")
                win_weight = float(prediction.get("win_weight", 1.0))
                loss_weight = float(prediction.get("loss_weight", 1.0))
                stats_win_weight = win_weight
                stats_loss_weight = loss_weight
                count_each_roll = bool(prediction.get("count_each_roll"))
                if bet_split:
                    prediction_state.strategy.validate(prediction, result)
                    matched = self._match_bet_split(bet_split, result)
                    win = matched is not None
                    if matched:
                        win_weight = float(matched.get("weight", 1.0))
                    stats_win_weight = 1.0
                    stats_loss_weight = 1.0
                else:
                    win = prediction_state.strategy.validate(prediction, result)
                registered_outcome = True
                strategy_stats = self._stats_for_strategy(strategy_name)
                if count_each_roll or not prediction_state.counted:
                    self.stats.register_result(
                        win,
                        win_weight=stats_win_weight,
                        loss_weight=stats_loss_weight,
                    )
                    strategy_stats.register_result(
                        win,
                        win_weight=stats_win_weight,
                        loss_weight=stats_loss_weight,
                    )
                    if not count_each_roll:
                        prediction_state.counted = True
                bank_snapshot = (
                    self.bank_manager.apply_result(
                        strategy_name,
                        win,
                        payout=win_weight,
                        loss_multiplier=loss_weight,
                    )
                    if self.bank_manager is not None
                    else None
                )
                for notifier in self.notifiers:
                    if hasattr(notifier, "evaluation"):
                        min_winrate = strategy_stats.min_winrate
                        max_winrate = strategy_stats.max_winrate
                        notifier.evaluation(
                            win,
                            result,
                            strategy_stats.winrate,
                            {
                                "entries": strategy_stats.total_entries,
                                "wins": strategy_stats.wins,
                                "losses": strategy_stats.losses,
                            },
                            strategy_name=strategy_name,
                            min_winrate=min_winrate,
                            max_winrate=max_winrate,
                            bank_snapshot=bank_snapshot,
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
                            min_winrate=strategy_stats.min_winrate,
                            max_winrate=strategy_stats.max_winrate,
                        )
                if not win and prediction_state.remaining_martingale > 0:
                    prediction_state.remaining_martingale -= 1
                    pending_predictions.append(prediction_state)
            if registered_outcome:
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
            self.last_predictions = pending_predictions
            if pending_predictions:
                for prediction_state in pending_predictions:
                    prediction_payload = {
                        **prediction_state.prediction,
                        "strategy": prediction_state.strategy_name,
                    }
                    for notifier in self.notifiers:
                        if hasattr(notifier, "prediction"):
                            notifier.prediction(prediction_payload)
                return

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
                    remaining_martingale=strategy.martingale_limit(),
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
                remaining_martingale=self.strategy.martingale_limit(),
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
