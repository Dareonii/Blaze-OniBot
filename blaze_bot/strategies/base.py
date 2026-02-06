from __future__ import annotations

from abc import ABC, abstractmethod
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class StrategyBase(ABC):
    MIN_WINRATE = 0.0
    MAX_WINRATE = 100.0
    MARTINGALE = 0

    def strategy_name(self) -> str:
        module = sys.modules.get(self.__class__.__module__)
        if module and hasattr(module, "__name__"):
            return module.__name__.split(".")[-1]
        return self.__class__.__name__

    def winrate_limits(self) -> tuple[float, float]:
        return (float(self.MIN_WINRATE), float(self.MAX_WINRATE))

    def martingale_limit(self) -> int:
        return max(0, int(self.MARTINGALE))

    @abstractmethod
    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recebe histórico e retorna decisão."""

    @abstractmethod
    def predict(
        self, history: List[Dict[str, Any]]
    ) -> Optional[Union[Dict[str, Any], Sequence[Dict[str, Any]]]]:
        """Retorna predição: cor/número ou lista de predições."""

    @abstractmethod
    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Retorna True (win) ou False (loss)."""


class MultiStrategy(StrategyBase):
    def __init__(self, strategies: List[StrategyBase]) -> None:
        if not strategies:
            raise ValueError("Nenhuma estratégia informada.")
        self._strategies = strategies
        self._last_strategy: Optional[StrategyBase] = None

    @property
    def strategies(self) -> List[StrategyBase]:
        return list(self._strategies)

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {}
        for strategy in self._strategies:
            analysis.update(strategy.analyze(history))
        return analysis

    def predict(
        self, history: List[Dict[str, Any]]
    ) -> Optional[Union[Dict[str, Any], Sequence[Dict[str, Any]]]]:
        predictions: List[Dict[str, Any]] = []
        for strategy, prediction in self._predictions_with_strategies(history):
            self._last_strategy = strategy
            predictions.append(prediction)
        return predictions or None

    def predictions_with_strategies(
        self, history: List[Dict[str, Any]]
    ) -> List[Tuple[StrategyBase, Dict[str, Any]]]:
        return self._predictions_with_strategies(history)

    def _predictions_with_strategies(
        self, history: List[Dict[str, Any]]
    ) -> List[Tuple[StrategyBase, Dict[str, Any]]]:
        predictions: List[Tuple[StrategyBase, Dict[str, Any]]] = []
        for strategy in self._strategies:
            self._last_strategy = strategy
            prediction = strategy.predict(history)
            if prediction is None:
                continue
            if isinstance(prediction, dict):
                predictions.append((strategy, prediction))
            else:
                predictions.extend(
                    [(strategy, item) for item in prediction if isinstance(item, dict)]
                )
        return predictions

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        if self._last_strategy is None:
            return False
        return self._last_strategy.validate(prediction, result)
