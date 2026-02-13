# TradeBot

A chat-style stock and crypto trading assistant powered by Azure OpenAI (gpt-5).

## Features

- **Balances** – View cash, non-cash (investments), and total portfolio value.
- **Positions / Holdings** – See all stocks and crypto you own, plus cash.
- **Transaction History** – Full log of buys, sells, and cancellations.
- **Trading** – Buy and sell stocks or crypto with natural language commands.
  - Orders start as *open* and execute automatically after a few seconds.
  - Margin orders are blocked — you can't spend more cash than you have or sell more than you own.
- **Cancel Orders** – Cancel any open order before it executes.
- **Order Status** – View open, cancelled, and today's executed orders.
- **Quotes** – Live prices from Yahoo Finance.
- **Insights** – AI-generated analysis of stocks/crypto using recent news headlines.
  - Warnings when a trade goes against current sentiment.

## Setup

1. **Clone and install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Azure OpenAI:**

   Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_DEPLOYMENT=gpt-5
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   ```

3. **Run the bot:**

   ```bash
   python main.py
   ```

## Usage Examples

```
You > show my balances
You > what are my positions?
You > buy 10 AAPL
You > sell 5 TSLA
You > get a quote for BTC
You > show insights for NVDA
You > cancel order ORD024
You > order status
You > show my transaction history
You > change my name to Alex
```

## Data Files

All state is persisted in `data/` as JSON:

| File | Contents |
|---|---|
| `balances.json` | Cash, non-cash, and total portfolio value |
| `positions.json` | Current stock/crypto holdings (15 initial records) |
| `orders.json` | Full order history (25 initial records) |
| `user.json` | User display name |

The bot reads and writes these files on every action, so you can stop and restart at any time without losing state.

## Architecture

| Module | Purpose |
|---|---|
| `main.py` | Entry point, chat loop, username prompt |
| `bot.py` | Azure OpenAI integration, function-calling dispatch |
| `trading.py` | Buy, sell, cancel, order status, background execution |
| `portfolio.py` | Balances and positions formatting |
| `quotes.py` | Yahoo Finance price quotes via yfinance |
| `insights.py` | AI-generated stock/crypto insights from news |
| `data_manager.py` | JSON file read/write with thread-safe locking |
| `config.py` | Environment variable loading |
