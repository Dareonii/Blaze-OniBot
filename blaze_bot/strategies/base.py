from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class StrategyBase(ABC):
    @abstractmethod
    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recebe histórico e retorna decisão."""

    @abstractmethod
    def predict(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retorna predição: cor/número."""

    @abstractmethod
    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Retorna True (win) ou False (loss)."""
