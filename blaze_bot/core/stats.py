from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Stats:
    total_entries: int = 0
    wins: int = 0
    losses: int = 0
    min_winrate: float | None = None
    max_winrate: float | None = None

    @property
    def winrate(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return (self.wins / self.total_entries) * 100

    def register_result(self, win: bool) -> None:
        self.total_entries += 1
        if win:
            self.wins += 1
        else:
            self.losses += 1
        current_winrate = self.winrate
        if self.min_winrate is None or current_winrate < self.min_winrate:
            self.min_winrate = current_winrate
        if self.max_winrate is None or current_winrate > self.max_winrate:
            self.max_winrate = current_winrate
