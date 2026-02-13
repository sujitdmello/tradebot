# TradeBot

A chat-style stock and crypto trading assistant powered by Azure OpenAI.

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
You > how can I invest 25000?
You > What should I buy for that money?
You > yes proceed with the trades
```

A snapshot from the running instance of the bot is shown below: 
```bash
Sujit > What should I buy for that money?

TradeBot > Sujit, here’s a balanced investment suggestion for your $25,000, considering current market sentiment and your existing portfolio:

1. Diversified Stocks (60% = $15,000)
   - Add to strong tech names you already own (AAPL, MSFT, NVDA) or diversify with new sectors (e.g., healthcare, financials).
   - Example: $5,000 each in AAPL, MSFT, and a new stock like UNH (UnitedHealth) or V (Visa).

2. ETFs (20% = $5,000)
   - Consider an S&P 500 ETF (SPY) or a tech ETF (QQQ) for broad market exposure and lower risk.

3. Cryptocurrency (10% = $2,500)
   - Add to BTC or ETH, or diversify with a smaller allocation to SOL or ADA, given your current holdings.

4. Dividend/Income Stocks (10% = $2,500)
   - Invest in dividend payers like JNJ, JPM, or a REIT ETF for income and stability.

Example Allocation:
- $5,000 AAPL
- $5,000 MSFT
- $5,000 UNH or V
- $5,000 SPY or QQQ
- $2,500 BTC or ETH
- $2,500 JNJ or JPM

This approach balances growth, diversification, and income, while aligning with current market sentiment (cautious optimism in tech, neutral in crypto, and steady in blue-chip/dividend stocks).

Would you like to proceed with this allocation, customize it, or focus on a specific area? Let me know your preferences, and I can help you place the trades!

Sujit > yes proceed with the trades

TradeBot > Your $25,000 investment is being allocated as follows (orders placed and will execute shortly):

- 23 AAPL ($5,938.60) – Note: Mixed sentiment, some near-term headwinds.
- 12 MSFT ($4,822.08) – Note: Cautious sentiment in tech/AI, but solid long-term.
- 16 V ($5,034.56) – Note: Positive sentiment, strong earnings, some fee pressure risks.
- 10 SPY ($6,831.50) – Note: Mixed short-term, positive long-term outlook.
- 0.05 BTC ($3,443.20) – Note: Mixed to bearish sentiment, higher near-term risk.
- 15 JNJ ($3,653.25) – Note: Leaning positive, some legal risks but strong fundamentals.

If you want to adjust or review any order, let me know. Otherwise, I’ll update you once these trades are executed!


[TradeBot] ✓ Order ORD027 executed: BUY 23.0 AAPL @ $258.2000 ($5,938.60).

[TradeBot] ✓ Order ORD028 executed: BUY 12.0 MSFT @ $401.8400 ($4,822.08).

[TradeBot] ✓ Order ORD029 executed: BUY 16.0 V @ $314.6601 ($5,034.56).

[TradeBot] ✓ Order ORD030 executed: BUY 10.0 SPY @ $683.1500 ($6,831.50).

[TradeBot] ✓ Order ORD031 executed: BUY 0.05 BTC @ $68,864.0312 ($3,443.20).
Sujit > order status

TradeBot > Here’s your latest order status, Sujit:

Executed Today:
- ORD027: Buy 23 AAPL @ $258.20
- ORD028: Buy 12 MSFT @ $401.84
- ORD029: Buy 16 V @ $314.66
- ORD030: Buy 10 SPY @ $683.15
- ORD031: Buy 0.05 BTC @ $68,864.03
- ORD032: Buy 15 JNJ @ $243.55
- ORD026: Sell 40 TSLA @ $420.30

Open Orders:
- ORD024: Buy 10 GOOGL @ $180.00
- ORD025: Sell 0.1 BTC @ $48,000.00

All your recent investment orders have been executed. Let me know if you want to review your updated portfolio or need further assistance!
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
