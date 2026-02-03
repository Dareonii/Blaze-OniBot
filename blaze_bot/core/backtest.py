from __future__ import annotations

from typing import Any, Dict, Iterable, List

from blaze_bot.core.stats import Stats
from blaze_bot.strategies.base import StrategyBase


def run_backtest(strategy: StrategyBase, history: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    stats = Stats()
    prediction: Dict[str, Any] | None = None
    buffered_history: List[Dict[str, Any]] = []

    for result in history:
        buffered_history.append(result)
        if prediction is not None:
            win = strategy.validate(prediction, result)
            stats.register_result(win)
        strategy.analyze(buffered_history)
        prediction = strategy.predict(buffered_history)

    return {
        "entries": stats.total_entries,
        "wins": stats.wins,
        "losses": stats.losses,
        "winrate": stats.winrate,
    }
