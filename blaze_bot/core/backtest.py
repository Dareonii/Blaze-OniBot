from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import MultiStrategy, StrategyBase


def run_backtest(strategy: StrategyBase, history: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    stats = Stats()
    strategy_stats: Dict[str, Stats] = {}
    predictions: List[tuple[StrategyBase, Dict[str, Any], int, bool, int]] = []
    buffered_history: List[Dict[str, Any]] = []
    martingale_carryover: Dict[str, Dict[str, int]] = {}

    def _carryover_for(strategy_name: str, default: int) -> tuple[int, int]:
        carry = martingale_carryover.get(strategy_name)
        if carry and carry.get("remaining", 0) > 0:
            return int(carry.get("remaining", default)), int(carry.get("step", 0))
        return default, 0

    for result in history:
        buffered_history.append(result)
        if predictions:
            pending: List[tuple[StrategyBase, Dict[str, Any], int, bool, int]] = []
            for prediction_strategy, prediction, remaining_martingale, counted, martingale_step in predictions:
                bet_split = prediction.get("bet_split")
                win_weight = float(prediction.get("win_weight", 1.0))
                loss_weight = float(prediction.get("loss_weight", 1.0))
                stats_win_weight = float(prediction.get("stats_win_weight", win_weight))
                stats_loss_weight = float(prediction.get("stats_loss_weight", loss_weight))
                count_each_roll = bool(prediction.get("count_each_roll"))
                entry_weight = prediction.get("entry_weight")
                if bet_split:
                    prediction_strategy.validate(prediction, result)
                    matched = _match_bet_split(bet_split, result)
                    win = matched is not None
                    if matched:
                        weight = float(matched.get("weight", 1.0))
                        payout = matched.get("payout")
                        if payout is None:
                            payout = _default_payout_for_color(matched.get("color"))
                        win_weight = weight * float(payout)
                    stats_win_weight = 1.0
                    stats_loss_weight = 1.0
                else:
                    win = prediction_strategy.validate(prediction, result)
                strategy_name = prediction_strategy.strategy_name()
                if win is None:
                    if remaining_martingale > 0:
                        martingale_carryover[strategy_name] = {
                            "remaining": remaining_martingale,
                            "step": martingale_step,
                        }
                    else:
                        martingale_carryover.pop(strategy_name, None)
                    continue
                strategy_stat = strategy_stats.get(strategy_name)
                if strategy_stat is None:
                    strategy_stat = Stats()
                    strategy_stats[strategy_name] = strategy_stat
                if count_each_roll or not counted:
                    stats.register_result(
                        win,
                        win_weight=stats_win_weight,
                        loss_weight=stats_loss_weight,
                        entry_weight=entry_weight,
                    )
                    strategy_stat.register_result(
                        win,
                        win_weight=stats_win_weight,
                        loss_weight=stats_loss_weight,
                        entry_weight=entry_weight,
                    )
                    if not count_each_roll:
                        counted = True
                if not win and remaining_martingale > 0:
                    pending.append(
                        (
                            prediction_strategy,
                            prediction,
                            remaining_martingale - 1,
                            counted,
                            martingale_step + 1,
                        )
                    )
                elif not win:
                    martingale_carryover.pop(strategy_name, None)
                else:
                    martingale_carryover.pop(strategy_name, None)
            predictions = pending
            if predictions:
                continue
        strategy.analyze(buffered_history)
        if isinstance(strategy, MultiStrategy):
            predictions = [
                (
                    item_strategy,
                    item_prediction,
                    _carryover_for(
                        item_strategy.strategy_name(),
                        item_strategy.martingale_limit(),
                    )[0],
                    False,
                    _carryover_for(
                        item_strategy.strategy_name(),
                        item_strategy.martingale_limit(),
                    )[1],
                )
                for item_strategy, item_prediction in strategy.predictions_with_strategies(
                    buffered_history
                )
            ]
        else:
            prediction = strategy.predict(buffered_history)
            normalized = _normalize_predictions(prediction)
            remaining, step = _carryover_for(
                strategy.strategy_name(), strategy.martingale_limit()
            )
            predictions = [
                (
                    strategy,
                    item,
                    remaining,
                    False,
                    step,
                )
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


def _match_bet_split(
    bet_split: Sequence[Dict[str, Any]], result: Dict[str, Any]
) -> Dict[str, Any] | None:
    result_color = result.get("color")
    for item in bet_split:
        if item.get("color") == result_color:
            return item
    return None


def _default_payout_for_color(color: Any) -> float:
    normalized = str(color).lower()
    mapping = {"white": 14.0, "red": 2.0, "black": 2.0}
    return mapping.get(normalized, 1.0)
