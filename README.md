# Blaze-OniBot

Bot modular para análise e predição do jogo Blaze Double. O foco é arquitetura limpa, estratégias plugáveis e saída via terminal/Telegram.

## Estrutura

```
blaze_bot/
├── core/
├── data/
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
- `TELEGRAM_BOT_TOKEN`: token do bot.
- `TELEGRAM_CHAT_ID`: chat ID para envio de mensagens.

## Uso

### Execução em tempo real

```
python -m blaze_bot.main
```

### Backtest

```
python -m blaze_bot.main --backtest-file caminho/para/historico.jsonl
```

O arquivo de histórico pode ser JSON (lista) ou JSONL (uma entrada por linha).
