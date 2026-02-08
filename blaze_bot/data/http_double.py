from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

import requests

logger = logging.getLogger(__name__)


def fetch_double_history(
    url: str,
    *,
    limit: int = 200,
    timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    try:
        response = requests.get(url, params={"limit": limit}, timeout=timeout)
        response.raise_for_status()
        payload: Any = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Falha ao buscar histórico do double: %s", exc)
        return []

    records = _extract_records(payload)
    if not records:
        return []

    normalized: List[Dict[str, Any]] = []
    for item in records:
        entry = _normalize_entry(item)
        if entry:
            normalized.append(entry)

    normalized = normalized[:limit]
    normalized.reverse()
    return normalized


def _extract_records(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _normalize_entry(item: Dict[str, Any]) -> Dict[str, Any] | None:
    color = item.get("color") if "color" in item else item.get("colour")
    number = item.get("roll") if "roll" in item else item.get("number")
    timestamp = (
        item.get("created_at")
        or item.get("createdAt")
        or item.get("timestamp")
        or item.get("created")
    )
    if color is None or number is None:
        return None
    return {
        "timestamp": timestamp,
        "number": int(number),
        "color": _normalize_color(color),
    }


def _normalize_color(color: Any) -> str:
    if isinstance(color, str):
        return color
    mapping = {0: "white", 1: "red", 2: "black"}
    return mapping.get(int(color), str(color))


def merge_histories(
    base: Iterable[Dict[str, Any]],
    incoming: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for entry in list(base) + list(incoming):
        signature = (entry.get("number"), entry.get("color"), entry.get("timestamp"))
        if signature in seen:
            continue
        seen.add(signature)
        merged.append(entry)
    return merged
