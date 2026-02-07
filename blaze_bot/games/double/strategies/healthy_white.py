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


class Strategy(StrategyBase):
    """Agenda duas janelas de aposta no branco após cada branco."""

    MARTINGALE = 0

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
        for event in self._events:
            phase = self._event_phase(event)
            if phase is None:
                continue
            return {
                "color": "white",
                "win_weight": 14,
                "loss_weight": 1,
                "count_each_roll": True,
                "event_id": event.event_id,
                "phase": phase,
            }
        return None

    def validate(self, prediction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        result_color = result.get("color")
        event_id = prediction.get("event_id")
        phase = prediction.get("phase")
        event = self._event_by_id(event_id)
        if event is None:
            return result_color == "white"

        if result_color == "white":
            if phase == "phase1":
                event.phase1_done = True
            elif phase == "phase2":
                event.phase2_done = True
        else:
            if phase == "phase1" and not event.phase1_done:
                event.phase1_attempts += 1
                if event.phase1_attempts >= self.MAX_ATTEMPTS:
                    event.phase1_done = True
            elif phase == "phase2" and not event.phase2_done:
                event.phase2_attempts += 1
                if event.phase2_attempts >= self.MAX_ATTEMPTS:
                    event.phase2_done = True
        self._cleanup_events()
        return result_color == "white"

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

    def _event_phase(self, event: WhiteEvent) -> Optional[str]:
        if not event.phase1_done and event.rolls_since >= self.PHASE1_DELAY:
            if event.phase1_attempts < self.MAX_ATTEMPTS:
                return "phase1"
        if event.phase1_done and not event.phase2_done:
            if event.rolls_since >= self.PHASE2_DELAY:
                if event.phase2_attempts < self.MAX_ATTEMPTS:
                    return "phase2"
        return None

    def _cleanup_events(self) -> None:
        self._events = [
            event
            for event in self._events
            if not (event.phase1_done and event.phase2_done)
        ]
