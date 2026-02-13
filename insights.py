"""Gather stock/crypto insights using Azure OpenAI + Yahoo Finance news."""

import yfinance as yf
from openai import AzureOpenAI

import config

_client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
)


def _fetch_news(symbol: str) -> list[str]:
    """Pull recent news headlines from Yahoo Finance for context."""
    yf_sym = symbol.upper()
    # Crypto mapping
    crypto_map = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
                  "ADA": "ADA-USD", "DOGE": "DOGE-USD"}
    yf_sym = crypto_map.get(yf_sym, yf_sym)

    ticker = yf.Ticker(yf_sym)
    headlines = []
    try:
        for item in (ticker.news or [])[:8]:
            title = item.get("title") or item.get("content", {}).get("title", "")
            if title:
                headlines.append(title)
    except Exception:
        pass
    return headlines


def get_insights(symbol: str) -> str:
    """Return AI-generated insights for a symbol based on recent news."""
    headlines = _fetch_news(symbol)
    news_block = "\n".join(f"- {h}" for h in headlines) if headlines else "No recent news found."

    resp = _client.chat.completions.create(
        model=config.AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial analyst assistant. Given recent news headlines "
                    "for a stock or crypto asset, provide a concise summary of the current "
                    "sentiment, key risks, and whether the asset looks favorable for buying "
                    "or selling right now. Be balanced and mention both bullish and bearish "
                    "factors. Keep it to 3-5 sentences."
                ),
            },
            {
                "role": "user",
                "content": f"Symbol: {symbol.upper()}\n\nRecent headlines:\n{news_block}",
            },
        ],
        temperature=0.4,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def check_trade_against_insights(symbol: str, action: str) -> str:
    """Warn the user if their intended trade conflicts with current insights."""
    headlines = _fetch_news(symbol)
    news_block = "\n".join(f"- {h}" for h in headlines) if headlines else "No recent news found."

    resp = _client.chat.completions.create(
        model=config.AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial risk advisor. The user wants to place a trade. "
                    "Based on the recent news headlines, determine whether the trade aligns "
                    "with current sentiment. If it goes against the prevailing sentiment, "
                    "provide a brief warning (2-3 sentences). If it aligns, confirm briefly. "
                    "Do NOT tell the user what to do — just inform them of the risk."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"The user wants to {action.upper()} {symbol.upper()}.\n\n"
                    f"Recent headlines:\n{news_block}"
                ),
            },
        ],
        temperature=0.3,
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()
