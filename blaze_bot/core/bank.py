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
        self.martingale_banks: Dict[str, float] = {}
        self.martingale_enabled: Dict[str, bool] = {}
        if not settings.enabled:
            return
        if settings.per_strategy:
            self.banks = {
                name: float(settings.initial_bank) for name in strategy_names
            }
            self.martingale_banks = dict(self.banks)
        else:
            self.banks = {"GERAL": float(settings.initial_bank)}
            self.martingale_banks = dict(self.banks)

    def apply_result(
        self,
        strategy_name: str,
        win: bool,
        *,
        payout: float = 1.0,
        loss_multiplier: float = 1.0,
        martingale_step: int = 0,
        martingale_factor: float = 1.0,
        martingale_active: bool = False,
    ) -> Dict[str, Dict[str, float | bool]] | None:
        if not self.settings.enabled:
            return None
        if self.settings.per_strategy:
            if strategy_name not in self.banks:
                self.banks[strategy_name] = float(self.settings.initial_bank)
                self.martingale_banks[strategy_name] = float(
                    self.settings.initial_bank
                )
            key = strategy_name
        else:
            key = next(iter(self.banks))
        current = self.banks[key]
        martingale_current = self.martingale_banks.get(key, current)
        bet = self._bet_amount(current)
        martingale_bet = bet * self._martingale_multiplier(
            martingale_step, martingale_factor, martingale_active
        )
        if win:
            payout = max(0.0, float(payout))
            self.banks[key] = current + (bet * payout)
            self.martingale_banks[key] = martingale_current + (martingale_bet * payout)
        else:
            loss_multiplier = max(0.0, float(loss_multiplier))
            self.banks[key] = current - (bet * loss_multiplier)
            self.martingale_banks[key] = (
                martingale_current - (martingale_bet * loss_multiplier)
            )
        self.martingale_enabled[key] = bool(martingale_active)
        return self.snapshot()

    def snapshot(self) -> Dict[str, Dict[str, float | bool]]:
        snapshot: Dict[str, Dict[str, float | bool]] = {}
        for name, value in self.banks.items():
            snapshot[name] = {
                "base": value,
                "martingale": self.martingale_banks.get(name, value),
                "martingale_enabled": self.martingale_enabled.get(name, False),
            }
        return snapshot

    def _bet_amount(self, current_bank: float) -> float:
        if self.settings.mode == "multiplicative":
            return current_bank * self.settings.bet_value
        return self.settings.bet_value

    @staticmethod
    def _martingale_multiplier(
        step: int, factor: float, active: bool
    ) -> float:
        if not active:
            return 1.0
        step = max(0, int(step))
        try:
            factor_value = float(factor)
        except (TypeError, ValueError):
            factor_value = 1.0
        factor_value = max(1.0, factor_value)
        if step == 0:
            return 1.0
        return factor_value**step
