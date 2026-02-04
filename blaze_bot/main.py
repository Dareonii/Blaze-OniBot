from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from blaze_bot.config.settings import Settings
from blaze_bot.core.backtest import run_backtest
from blaze_bot.core.engine import Engine
from blaze_bot.data.websocket_double import BlazeDoubleWebSocket
from blaze_bot.notifications.terminal import TerminalNotifier
from blaze_bot.notifications.telegram import TelegramNotifier
from blaze_bot.strategies import available_strategies, build_strategy


def load_history(path: Path) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("["):
        return json.loads(raw)
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def build_notifiers(settings: Settings) -> list[Any]:
    notifiers: list[Any] = [TerminalNotifier()]
    if settings.telegram_token and settings.telegram_chat_id:
        notifiers.append(TelegramNotifier(settings.telegram_token, settings.telegram_chat_id))
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
        print(
            "[BACKTEST:{name}] Entradas: {entries} | Wins: {wins} | Losses: {losses} | Winrate: {winrate:.2f}%".format(
                name=name,
                entries=stats["entries"],
                wins=stats["wins"],
                losses=stats["losses"],
                winrate=stats["winrate"],
            )
        )


def run_live(settings: Settings, strategy: Any) -> None:
    async def _run() -> None:
        notifiers = build_notifiers(settings)
        engine = Engine(strategy=strategy, notifiers=notifiers)
        socket = BlazeDoubleWebSocket(
            settings.websocket_url,
            token=settings.websocket_token,
            room=settings.websocket_room,
            reconnect_backoff_initial=settings.websocket_reconnect_backoff_initial,
            reconnect_backoff_max=settings.websocket_reconnect_backoff_max,
        )
        stream = socket.listen()
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
            engine.process_result(result)

    asyncio.run(_run())


def prompt_strategies() -> Any:
    strategies = available_strategies()
    if not strategies:
        raise ValueError("Nenhuma estratégia disponível na pasta strategies.")
    unique_names = sorted({name for name in strategies.keys()})
    available_display = ", ".join(unique_names)
    raw = input(
        "Informe as estratégias (separadas por vírgula). "
        f"Disponíveis: {available_display}. "
        "Pressione Enter para usar a primeira disponível: "
    ).strip()
    if not raw:
        chosen = [unique_names[0]]
    else:
        chosen = [name.strip() for name in raw.split(",") if name.strip()]
    return build_strategy(chosen)


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
        strategy = prompt_strategies()
        run_backtest_mode(strategy, history)
        return

    strategy = prompt_strategies()
    run_live(settings, strategy)


if __name__ == "__main__":
    main()
