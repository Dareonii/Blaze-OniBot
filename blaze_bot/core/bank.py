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
        self.min_banks: Dict[str, float] = {}
        self.max_banks: Dict[str, float] = {}
        self.min_martingale_banks: Dict[str, float] = {}
        self.max_martingale_banks: Dict[str, float] = {}
        self.gales_count: Dict[str, int] = {}
        self.max_gale_level: Dict[str, int] = {}
        self.last_martingale_bets: Dict[str, float] = {}
        if not settings.enabled:
            return
        if settings.per_strategy:
            for name in strategy_names:
                self._initialize_strategy(name, float(settings.initial_bank))
        else:
            self._initialize_strategy("GERAL", float(settings.initial_bank))

    def _initialize_strategy(self, name: str, initial_bank: float) -> None:
        self.banks[name] = float(initial_bank)
        self.martingale_banks[name] = float(initial_bank)
        self.min_banks[name] = float(initial_bank)
        self.max_banks[name] = float(initial_bank)
        self.min_martingale_banks[name] = float(initial_bank)
        self.max_martingale_banks[name] = float(initial_bank)
        self.gales_count[name] = 0
        self.max_gale_level[name] = 0
        self.last_martingale_bets[name] = 0.0

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
                self._initialize_strategy(
                    strategy_name, float(self.settings.initial_bank)
                )
            key = strategy_name
        else:
            key = next(iter(self.banks))
        current = self.banks[key]
        martingale_current = self.martingale_banks.get(key, current)
        bet = self._bet_amount(current)
        martingale_bet = self._martingale_bet_amount(
            key,
            martingale_current,
            bet,
            martingale_step,
            martingale_factor,
            martingale_active,
        )
        if martingale_active and martingale_step > 0:
            self.gales_count[key] = self.gales_count.get(key, 0) + 1
            self.max_gale_level[key] = max(
                self.max_gale_level.get(key, 0), int(martingale_step)
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
        self._update_min_max(key)
        return self.snapshot()

    def snapshot(self) -> Dict[str, Dict[str, float | bool]]:
        snapshot: Dict[str, Dict[str, float | bool]] = {}
        for name, value in self.banks.items():
            snapshot[name] = {
                "base": value,
                "martingale": self.martingale_banks.get(name, value),
                "martingale_enabled": self.martingale_enabled.get(name, False),
                "base_min": self.min_banks.get(name, value),
                "base_max": self.max_banks.get(name, value),
                "martingale_min": self.min_martingale_banks.get(name, value),
                "martingale_max": self.max_martingale_banks.get(name, value),
                "gales": self.gales_count.get(name, 0),
                "max_gale": self.max_gale_level.get(name, 0),
            }
        return snapshot

    def _bet_amount(self, current_bank: float) -> float:
        if self.settings.mode == "multiplicative":
            return current_bank * self.settings.bet_value
        return self.settings.bet_value

    def _martingale_bet_amount(
        self,
        key: str,
        current_bank: float,
        base_bet: float,
        step: int,
        factor: float,
        active: bool,
    ) -> float:
        if not active:
            self.last_martingale_bets[key] = base_bet
            return base_bet
        step = max(0, int(step))
        try:
            factor_value = float(factor)
        except (TypeError, ValueError):
            factor_value = 1.0
        factor_value = max(1.0, factor_value)
        if step == 0:
            bet = self._bet_amount(current_bank)
            self.last_martingale_bets[key] = bet
            return bet
        previous_bet = self.last_martingale_bets.get(key)
        if previous_bet is None or previous_bet <= 0:
            previous_bet = self._bet_amount(current_bank)
        bet = previous_bet * factor_value
        self.last_martingale_bets[key] = bet
        return bet

    def _update_min_max(self, key: str) -> None:
        current = self.banks.get(key)
        if current is not None:
            self.min_banks[key] = min(self.min_banks.get(key, current), current)
            self.max_banks[key] = max(self.max_banks.get(key, current), current)
        martingale_current = self.martingale_banks.get(key)
        if martingale_current is not None:
            self.min_martingale_banks[key] = min(
                self.min_martingale_banks.get(key, martingale_current),
                martingale_current,
            )
            self.max_martingale_banks[key] = max(
                self.max_martingale_banks.get(key, martingale_current),
                martingale_current,
            )
