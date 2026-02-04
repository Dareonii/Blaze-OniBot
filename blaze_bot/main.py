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
from blaze_bot.strategies.dummy import DummyAlternatingStrategy


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


def run_backtest_mode(history: Iterable[Dict[str, Any]]) -> None:
    strategy = DummyAlternatingStrategy()
    results = run_backtest(strategy, history)
    print(
        "[BACKTEST] Entradas: {entries} | Wins: {wins} | Losses: {losses} | Winrate: {winrate:.2f}%".format(
            entries=results["entries"],
            wins=results["wins"],
            losses=results["losses"],
            winrate=results["winrate"],
        )
    )


def run_live(settings: Settings) -> None:
    async def _run() -> None:
        strategy = DummyAlternatingStrategy()
        notifiers = build_notifiers(settings)
        engine = Engine(strategy=strategy, notifiers=notifiers)
        socket = BlazeDoubleWebSocket(settings.websocket_url)
        stream = socket.listen()
        while True:
            try:
                result = await asyncio.wait_for(stream.__anext__(), timeout=60)
            except asyncio.TimeoutError:
                for notifier in notifiers:
                    if hasattr(notifier, "warning"):
                        notifier.warning("Nenhum novo resultado recebido após 60s.")
                continue
            except StopAsyncIteration:
                break
            engine.process_result(result)

    asyncio.run(_run())


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    settings = Settings.from_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.backtest_file:
        history = load_history(args.backtest_file)
        run_backtest_mode(history)
        return

    run_live(settings)


if __name__ == "__main__":
    main()
