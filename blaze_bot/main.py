from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from blaze_bot.config.settings import Settings
from blaze_bot.core.backtest import run_backtest
from blaze_bot.core.engine import Engine
from blaze_bot.games import GameConfig, available_games
from blaze_bot.games.strategies import available_strategies, build_strategy
from blaze_bot.strategies.base import MultiStrategy
from blaze_bot.notifications.terminal import TerminalNotifier
from blaze_bot.notifications.telegram import TelegramNotifier


@dataclass(frozen=True)
class GameSession:
    game: GameConfig
    strategy: Any


def load_history(path: Path) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("["):
        return json.loads(raw)
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def build_notifiers(settings: Settings, game_label: str) -> list[Any]:
    notifiers: list[Any] = [TerminalNotifier()]
    if settings.telegram_token and settings.telegram_chat_id:
        notifiers.append(
            TelegramNotifier(settings.telegram_token, settings.telegram_chat_id, game_label)
        )
    return notifiers


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Blaze Double bot")
    parser.add_argument(
        "--backtest-file",
        type=Path,
        help="Arquivo JSON/JSONL com histórico para backtest",
    )
    return parser


def run_backtest_mode(strategy: Any, history: Iterable[Dict[str, Any]]) -> None:
    results = run_backtest(strategy, history)
    print(
        "[BACKTEST] Entradas: {entries} | Wins: {wins} | Losses: {losses} | Winrate: {winrate:.2f}%".format(
            entries=results["entries"],
            wins=results["wins"],
            losses=results["losses"],
            winrate=results["winrate"],
        )
    )
    per_strategy = results.get("per_strategy", {})
    for name, stats in per_strategy.items():
        min_winrate, max_winrate = _winrate_limits_for(strategy, name)
        print(
            "[BACKTEST:{name}] Entradas: {entries} | Wins: {wins} | Losses: {losses} | "
            "Winrate: {winrate:.2f}% (mín: {min_winrate:.2f}% | máx: {max_winrate:.2f}%)".format(
                name=name,
                entries=stats["entries"],
                wins=stats["wins"],
                losses=stats["losses"],
                winrate=stats["winrate"],
                min_winrate=min_winrate,
                max_winrate=max_winrate,
            )
        )


def run_live(settings: Settings, sessions: Iterable[GameSession]) -> None:
    async def _run_game(session: GameSession) -> None:
        notifiers = build_notifiers(settings, session.game.label)
        engine = Engine(strategy=session.strategy, notifiers=notifiers)
        strategy_names = _strategy_names(session.strategy)
        for notifier in notifiers:
            if hasattr(notifier, "startup"):
                notifier.startup(strategy_names)
        backtest_path = create_backtest_path(session.game.key)
        print(f"[BACKTEST] Gravando resultados em {backtest_path}")
        socket = session.game.socket_builder(settings)
        stream = socket.listen()
        with backtest_path.open("a", encoding="utf-8") as backtest_file:
            while True:
                try:
                    result = await asyncio.wait_for(
                        stream.__anext__(), timeout=settings.websocket_result_timeout
                    )
                except asyncio.TimeoutError:
                    for notifier in notifiers:
                        if hasattr(notifier, "warning"):
                            notifier.warning(
                                f"Nenhum novo resultado recebido após {settings.websocket_result_timeout:.0f}s."
                            )
                    continue
                except StopAsyncIteration:
                    break
                backtest_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                backtest_file.flush()
                engine.process_result(result)

    async def _run_all() -> None:
        tasks = [asyncio.create_task(_run_game(session)) for session in sessions]
        if not tasks:
            return
        await asyncio.gather(*tasks)

    asyncio.run(_run_all())


def prompt_games() -> List[GameConfig]:
    games = available_games()
    if not games:
        raise ValueError("Nenhum jogo disponível.")
    game_keys = sorted(games.keys())
    available_display = ", ".join(
        f"{key} ({games[key].label})" for key in game_keys
    )
    raw = input(
        "Informe os jogos (separados por vírgula). "
        f"Disponíveis: {available_display}. "
        "Pressione Enter para usar o primeiro disponível: "
    ).strip()
    if not raw:
        chosen = [game_keys[0]]
    else:
        chosen = [name.strip().lower() for name in raw.split(",") if name.strip()]
    selected_games = []
    missing = []
    for name in chosen:
        game = games.get(name)
        if game is None:
            missing.append(name)
        else:
            selected_games.append(game)
    if missing:
        raise ValueError(f"Jogos não encontrados: {', '.join(missing)}")
    return selected_games


def prompt_strategies(game: GameConfig) -> Any:
    strategies = available_strategies(game.strategy_package)
    if not strategies:
        raise ValueError(f"Nenhuma estratégia disponível para {game.label}.")
    unique_names = sorted({name for name in strategies.keys()})
    available_display = ", ".join(unique_names)
    raw = input(
        f"Informe as estratégias para {game.label} (separadas por vírgula). "
        f"Disponíveis: {available_display}. "
        "Pressione Enter para usar a primeira disponível: "
    ).strip()
    if not raw:
        chosen = [unique_names[0]]
    else:
        chosen = [name.strip() for name in raw.split(",") if name.strip()]
    return build_strategy(chosen, game.strategy_package)


def create_backtest_path(game_key: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    directory = Path(__file__).resolve().parent / "data" / "backtests"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"backtest_{game_key}_{timestamp}.jsonl"


def _winrate_limits_for(strategy: Any, strategy_name: str) -> tuple[float, float]:
    if hasattr(strategy, "strategy_name") and strategy.strategy_name() == strategy_name:
        return strategy.winrate_limits()
    if isinstance(strategy, MultiStrategy):
        for item in strategy.strategies:
            if item.strategy_name() == strategy_name:
                return item.winrate_limits()
    return (0.0, 100.0)


def _strategy_names(strategy: Any) -> List[str]:
    if isinstance(strategy, MultiStrategy):
        return [item.strategy_name() for item in strategy.strategies]
    if hasattr(strategy, "strategy_name"):
        return [strategy.strategy_name()]
    return []


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    settings = Settings.from_env()
    debug_choice = input("Ativar logs de INFO/WARNING? (y/n): ").strip().lower()
    debug_enabled = debug_choice in {"y", "yes", "s", "sim"}
    logging.basicConfig(
        level=logging.INFO if debug_enabled else logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.backtest_file:
        history = load_history(args.backtest_file)
        selected_games = prompt_games()
        sessions = [GameSession(game=game, strategy=prompt_strategies(game)) for game in selected_games]
        if len(sessions) > 1:
            raise ValueError("Backtest suporta apenas um jogo por vez.")
        run_backtest_mode(sessions[0].strategy, history)
        return

    selected_games = prompt_games()
    sessions = [GameSession(game=game, strategy=prompt_strategies(game)) for game in selected_games]
    run_live(settings, sessions)


if __name__ == "__main__":
    main()
