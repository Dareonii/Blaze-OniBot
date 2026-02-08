# Blaze-OniBot

Bot modular para análise e predição do jogo Blaze Double. O foco é arquitetura limpa, estratégias plugáveis e saída via terminal/Telegram.

## Estrutura

```
blaze_bot/
├── core/
├── data/
├── games/
│   └── double/
│       └── strategies/
├── strategies/
├── notifications/
├── config/
└── main.py
```

## Requisitos

- Python 3.10+
- Dependências em `requirements.txt`

## Configuração

Variáveis de ambiente suportadas:

- `BLAZE_DOUBLE_WS`: URL do WebSocket da Blaze Double.
- `BLAZE_DOUBLE_TOKEN`: token JWT usado para autenticar no socket (quando necessário).
- `BLAZE_DOUBLE_ROOM`: sala para inscrição no Socket.IO (padrão: `double_room_1`).
- `TELEGRAM_BOT_TOKEN`: token do bot.
- `TELEGRAM_CHAT_ID`: chat ID para envio de mensagens.

## Uso

### Execução em tempo real

```
python -m blaze_bot.main
```

Ao iniciar, o bot perguntará quais jogos e estratégias deseja executar.
Cada sessão em tempo real grava automaticamente um arquivo JSONL em
`blaze_bot/data/backtests/`.

### Backtest

```
python -m blaze_bot.main --backtest-file caminho/para/historico.jsonl
```

O arquivo de histórico pode ser JSON (lista) ou JSONL (uma entrada por linha).

Double é um jogo onde você deve escolher entre 3 cores(vermelho, preto e branco). Se você escolher a cor correta, ganhará 2x(preto ou vermelho) ou 14x(branco) o valor da aposta. Porém, se você escolher a cor errada, perde sua aposta. Você pode fazer múltiplas apostas em várias cores. As chances são ~46,67% para preto/vermelho e ~6,67% para branco. Acontece uma rodada a cada 30s.
