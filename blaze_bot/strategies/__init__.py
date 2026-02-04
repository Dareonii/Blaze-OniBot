from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Dict, Iterable, Type

from blaze_bot.strategies.base import MultiStrategy, StrategyBase

_IGNORED_MODULES = {"__init__", "base"}


def available_strategies() -> Dict[str, Type[StrategyBase]]:
    strategies: Dict[str, Type[StrategyBase]] = {}
    package_path = Path(__file__).resolve().parent
    for path in package_path.iterdir():
        if path.suffix != ".py" or path.stem in _IGNORED_MODULES:
            continue
        module_name = path.stem
        module = import_module(f"{__name__}.{module_name}")
        strategy_name = getattr(module, "STRATEGY_NAME", module_name)
        strategy_class = getattr(module, "Strategy", None)
        if strategy_class is None or not issubclass(strategy_class, StrategyBase):
            raise ValueError(
                f"Estratégia inválida em {module_name}: defina STRATEGY_NAME e class Strategy."
            )
        for key in {module_name.lower(), str(strategy_name).lower()}:
            if key in strategies and strategies[key] is not strategy_class:
                raise ValueError(f"Nome de estratégia duplicado: {key}")
            strategies[key] = strategy_class
    return strategies


def build_strategy(names: Iterable[str]) -> StrategyBase:
    available = available_strategies()
    selected: list[StrategyBase] = []
    missing = []
    for raw_name in names:
        name = raw_name.strip().lower()
        if not name:
            continue
        strategy_class = available.get(name)
        if strategy_class is None:
            missing.append(raw_name)
        else:
            selected.append(strategy_class())
    if missing:
        raise ValueError(f"Estratégias não encontradas: {', '.join(missing)}")
    if not selected:
        raise ValueError("Nenhuma estratégia selecionada.")
    if len(selected) == 1:
        return selected[0]
    return MultiStrategy(selected)
