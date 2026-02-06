from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class BankSettings:
    enabled: bool = True
    initial_bank: int = 100
    per_strategy: bool = True
    mode: str = "additive"
    bet_value: float = 1.0


class BankManager:
    def __init__(self, settings: BankSettings, strategy_names: Iterable[str]) -> None:
        self.settings = settings
        self.banks: Dict[str, float] = {}
        if not settings.enabled:
            return
        if settings.per_strategy:
            self.banks = {
                name: float(settings.initial_bank) for name in strategy_names
            }
        else:
            self.banks = {"GERAL": float(settings.initial_bank)}

    def apply_result(self, strategy_name: str, win: bool) -> Dict[str, float] | None:
        if not self.settings.enabled:
            return None
        if self.settings.per_strategy:
            if strategy_name not in self.banks:
                self.banks[strategy_name] = float(self.settings.initial_bank)
            key = strategy_name
        else:
            key = next(iter(self.banks))
        current = self.banks[key]
        bet = self._bet_amount(current)
        self.banks[key] = current + bet if win else current - bet
        return dict(self.banks)

    def snapshot(self) -> Dict[str, float]:
        return dict(self.banks)

    def _bet_amount(self, current_bank: float) -> float:
        if self.settings.mode == "multiplicative":
            return current_bank * self.settings.bet_value
        return self.settings.bet_value
