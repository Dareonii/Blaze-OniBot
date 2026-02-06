from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import MultiStrategy, StrategyBase


def run_backtest(strategy: StrategyBase, history: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    stats = Stats()
    strategy_stats: Dict[str, Stats] = {}
    predictions: List[tuple[StrategyBase, Dict[str, Any], int, bool]] = []
    buffered_history: List[Dict[str, Any]] = []

    for result in history:
        buffered_history.append(result)
        if predictions:
            pending: List[tuple[StrategyBase, Dict[str, Any], int, bool]] = []
            for prediction_strategy, prediction, remaining_martingale, counted in predictions:
                win = prediction_strategy.validate(prediction, result)
                strategy_name = prediction_strategy.strategy_name()
                strategy_stat = strategy_stats.get(strategy_name)
                if strategy_stat is None:
                    strategy_stat = Stats()
                    strategy_stats[strategy_name] = strategy_stat
                if not counted:
                    win_weight = prediction.get("win_weight", 1)
                    loss_weight = prediction.get("loss_weight", 1)
                    stats.register_result(
                        win, win_weight=win_weight, loss_weight=loss_weight
                    )
                    strategy_stat.register_result(
                        win, win_weight=win_weight, loss_weight=loss_weight
                    )
                    counted = True
                if not win and remaining_martingale > 0:
                    pending.append(
                        (prediction_strategy, prediction, remaining_martingale - 1, counted)
                    )
            predictions = pending
            if predictions:
                continue
        strategy.analyze(buffered_history)
        if isinstance(strategy, MultiStrategy):
            predictions = [
                (
                    item_strategy,
                    item_prediction,
                    item_strategy.martingale_limit(),
                    False,
                )
                for item_strategy, item_prediction in strategy.predictions_with_strategies(
                    buffered_history
                )
            ]
        else:
            prediction = strategy.predict(buffered_history)
            normalized = _normalize_predictions(prediction)
            predictions = [
                (strategy, item, strategy.martingale_limit(), False)
                for item in normalized
            ]

    return {
        "entries": stats.total_entries,
        "wins": stats.wins,
        "losses": stats.losses,
        "winrate": stats.winrate,
        "per_strategy": {
            name: {
                "entries": stat.total_entries,
                "wins": stat.wins,
                "losses": stat.losses,
                "winrate": stat.winrate,
            }
            for name, stat in strategy_stats.items()
        },
    }


def _normalize_predictions(
    prediction: Dict[str, Any] | Sequence[Dict[str, Any]] | None,
) -> List[Dict[str, Any]]:
    if prediction is None:
        return []
    if isinstance(prediction, dict):
        return [prediction]
    return [item for item in prediction if item]
