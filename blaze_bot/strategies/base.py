from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StrategyBase(ABC):
    STRATEGY_NAME = ""

    def strategy_name(self) -> str:
        return self.STRATEGY_NAME or self.__class__.__name__

    @abstractmethod
    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recebe histórico e retorna decisão."""

    @abstractmethod
    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Retorna predição: cor/número."""

    @abstractmethod
    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Retorna True (win) ou False (loss)."""


class MultiStrategy(StrategyBase):
    def __init__(self, strategies: List[StrategyBase]) -> None:
        if not strategies:
            raise ValueError("Nenhuma estratégia informada.")
        self._strategies = strategies
        self._next_index = 0
        self._last_strategy: Optional[StrategyBase] = None

    def strategy_name(self) -> str:
        if self._last_strategy is None:
            return "MultiStrategy"
        return self._last_strategy.strategy_name()

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {}
        for strategy in self._strategies:
            analysis.update(strategy.analyze(history))
        return analysis

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        strategy = self._strategies[self._next_index]
        self._next_index = (self._next_index + 1) % len(self._strategies)
        self._last_strategy = strategy
        return strategy.predict(history)

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        if self._last_strategy is None:
            return False
        return self._last_strategy.validate(prediction, result)
