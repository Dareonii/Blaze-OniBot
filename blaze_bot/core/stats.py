from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass
class Stats:
    WINDOW_SIZE = 50
    total_entries: int = 0
    wins: int = 0
    losses: int = 0
    min_winrate: float | None = None
    max_winrate: float | None = None
    _recent_winrates: Deque[float] = field(
        default_factory=lambda: deque(maxlen=Stats.WINDOW_SIZE),
        init=False,
        repr=False,
    )

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
        self._recent_winrates.append(current_winrate)
        if len(self._recent_winrates) < self.WINDOW_SIZE:
            self.min_winrate = None
            self.max_winrate = None
            return
        self.min_winrate = min(self._recent_winrates)
        self.max_winrate = max(self._recent_winrates)
