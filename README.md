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
- `BLAZE_DOUBLE_HISTORY_URL`: endpoint HTTP para recuperar histórico do Double (padrão: `https://api-gaming.blaze.bet.br/api/roulette_games/recent`).
- `BLAZE_DOUBLE_HISTORY_LIMIT`: quantidade máxima de resultados pré-carregados (padrão: `200`).
- `BLAZE_DOUBLE_HISTORY_TIMEOUT`: timeout (segundos) para a chamada de histórico (padrão: `10`).
- `BLAZE_DOUBLE_PRELOAD_HISTORY`: ativa o pré-carregamento de histórico (`true`/`false`).
- `TELEGRAM_BOT_TOKEN`: token do bot.
- `TELEGRAM_CHAT_ID`: chat ID para envio de mensagens.

## Uso

### Execução em tempo real

```
python -m blaze_bot.main
```

Ao iniciar, o bot perguntará quais jogos e estratégias deseja executar.
Se `BLAZE_DOUBLE_PRELOAD_HISTORY` estiver ativo, o bot pré-carrega o histórico
do dia antes de abrir o WebSocket.
Cada sessão em tempo real grava automaticamente um arquivo JSONL em
`blaze_bot/data/backtests/`.

### Backtest

```
python -m blaze_bot.main --backtest-file caminho/para/historico.jsonl
```

O arquivo de histórico pode ser JSON (lista) ou JSONL (uma entrada por linha).

Double é um jogo onde você deve escolher entre 3 cores(vermelho, preto e branco). Se você escolher a cor correta, ganhará 2x(preto ou vermelho) ou 14x(branco) o valor da aposta. Porém, se você escolher a cor errada, perde sua aposta. Você pode fazer múltiplas apostas em várias cores. As chances são ~46,67% para preto/vermelho e ~6,67% para branco. Acontece uma rodada a cada 30s.

## Estratégias disponíveis (Double)

Cada estratégia abaixo descreve a lógica de entrada usada no bot. Os nomes
correspondem aos módulos em `blaze_bot/games/double/strategies`.

### Balance Reversion (balance_reversion)

Observa uma janela curta (12 resultados) e aposta na cor menos frequente quando
há diferença mínima de 4 entre vermelho e preto. A ideia é buscar uma
“reversão” quando uma cor ficou muito acima da outra no curto prazo.

### Streak Rider (streak_rider)

Segue uma sequência curta (streak) de vermelho ou preto, ignorando o branco.
Entra quando a sequência atual tem entre 3 e 6 resultados seguidos, apostando
na continuidade dessa mesma cor.

### Healthy White (healthy_white)

Após cada branco, agenda duas “janelas” futuras de tentativa no branco: uma
após 16 rodadas e outra após 36 rodadas. Cada janela tenta até 10 entradas e é
desativada quando atinge o limite de tentativas ou quando o branco ocorre.
Serve para capturar brancos em ciclos posteriores ao último branco.

### White Gap Hedge (white_gap_hedge)

Identifica gaps longos sem branco (18+ rodadas). Quando isso ocorre, verifica
se uma cor domina as últimas 10 rodadas (pelo menos 7). Se sim, faz hedge:
aposta principalmente na cor dominante, com uma fatia menor no branco, para
cobrir o possível retorno do branco após um grande gap.

### White Coming (white_coming)

Procura dominância extrema em 20 rodadas (14+ do mesmo resultado). Quando
detecta esse cenário e não está em operação, sinaliza entrada no branco e
mantém o sinal ativo até o branco ocorrer ou até 14 tentativas consecutivas.
É uma leitura de “excesso” de uma cor como possível gatilho para branco.

### Supremacia (supremacia)

Detecta quando uma cor domina 20 rodadas (14+ do mesmo resultado; 13+ se saiu
um branco na janela). Ao identificar dominância, entra com aposta dividida:
majoritariamente na cor dominante e uma fração no branco. O sinal é encerrado
após 3 perdas seguidas fora da cor dominante (branco não conta como perda).

### Supremacia Pure (supremacia_pure)

Mesma lógica de dominância de 20 rodadas da Supremacia, mas com aposta simples
apenas na cor dominante. O sinal também é encerrado após 3 perdas seguidas.

### Dummy (dummy)

Estratégia simples para testes: alterna entre vermelho e preto a cada rodada,
ignorando o branco. Serve como referência básica de funcionamento.
