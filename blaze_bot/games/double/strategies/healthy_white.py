from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from blaze_bot.strategies.base import StrategyBase


@dataclass
class WhiteEvent:
    event_id: int
    rolls_since: int = 0
    phase1_attempts: int = 0
    phase2_attempts: int = 0
    phase1_done: bool = False
    phase2_done: bool = False

    def mark_completed(self) -> None:
        self.phase1_done = True
        self.phase2_done = True


class Strategy(StrategyBase):
    """Agenda duas janelas de aposta no branco após cada branco."""

    MARTINGALE = 20
    MARTINGALE_FACTOR = 1.1

    PHASE1_DELAY = 16
    PHASE2_DELAY = 36
    MAX_ATTEMPTS = 10

    def __init__(self) -> None:
        self._events: List[WhiteEvent] = []
        self._last_history_len = 0
        self._next_event_id = 1

    def analyze(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not history:
            self._last_history_len = 0
            return {"pending_events": 0}

        new_results = history[self._last_history_len :]
        for result in new_results:
            self._advance_events(result)
        self._last_history_len = len(history)
        self._cleanup_events()
        return {"pending_events": len(self._events)}

    def predict(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        active_events = []
        for event in self._events:
            for phase in self._active_phases(event):
                active_events.append({"event_id": event.event_id, "phase": phase})
        if active_events:
            return {
                "color": "white",
                "win_weight": 14,
                "loss_weight": 1,
                "stats_win_weight": 1,
                "stats_loss_weight": 1,
                "entry_weight": 1,
                "count_each_roll": True,
                "events": active_events,
            }
        return None

    def validate(
        self, prediction: Dict[str, Any], result: Dict[str, Any]
    ) -> bool | None:
        result_color = result.get("color")
        events = prediction.get("events")
        if not isinstance(events, list):
            events = []
        if not events:
            return result_color == "white"

        active_events: List[tuple[WhiteEvent, str]] = []
        for event_item in events:
            event_id = event_item.get("event_id")
            phase = event_item.get("phase")
            event = self._event_by_id(event_id)
            if event is None:
                continue
            if phase in self._active_phases(event):
                active_events.append((event, phase))
        if not active_events:
            return None
        if result_color == "white":
            for event, _phase in active_events:
                event.mark_completed()
            self._cleanup_events()
            return True

        for event, phase in active_events:
            if phase == "phase1" and not event.phase1_done:
                event.phase1_attempts += 1
                if event.phase1_attempts >= self.MAX_ATTEMPTS:
                    event.phase1_done = True
            elif phase == "phase2" and not event.phase2_done:
                event.phase2_attempts += 1
                if event.phase2_attempts >= self.MAX_ATTEMPTS:
                    event.phase2_done = True
        self._cleanup_events()
        return False

    def _advance_events(self, result: Dict[str, Any]) -> None:
        for event in self._events:
            event.rolls_since += 1
        if result.get("color") == "white":
            self._events.append(WhiteEvent(event_id=self._next_event_id))
            self._next_event_id += 1

    def _event_by_id(self, event_id: object) -> Optional[WhiteEvent]:
        if not isinstance(event_id, int):
            return None
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None

    def _active_phases(self, event: WhiteEvent) -> List[str]:
        phases: List[str] = []
        if not event.phase1_done and event.rolls_since >= self.PHASE1_DELAY:
            if event.phase1_attempts < self.MAX_ATTEMPTS:
                phases.append("phase1")
        if not event.phase2_done and event.rolls_since >= self.PHASE2_DELAY:
            if event.phase2_attempts < self.MAX_ATTEMPTS:
                phases.append("phase2")
        return phases

    def _cleanup_events(self) -> None:
        self._events = [
            event
            for event in self._events
            if not (event.phase1_done and event.phase2_done)
        ]
