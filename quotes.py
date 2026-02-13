"""Fetch live quotes from Yahoo Finance using yfinance."""

import yfinance as yf

# Crypto symbols need special suffixes for Yahoo Finance
_CRYPTO_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "ADA": "ADA-USD",
    "DOGE": "DOGE-USD",
    "XRP": "XRP-USD",
    "DOT": "DOT-USD",
    "AVAX": "AVAX-USD",
    "MATIC": "MATIC-USD",
    "LINK": "LINK-USD",
    "SHIB": "SHIB-USD",
}


def _yahoo_symbol(symbol: str) -> str:
    upper = symbol.upper()
    return _CRYPTO_MAP.get(upper, upper)


def get_quote(symbol: str) -> dict:
    """Return price info for a single symbol."""
    yf_sym = _yahoo_symbol(symbol)
    ticker = yf.Ticker(yf_sym)
    info = ticker.fast_info
    try:
        price = info.last_price
        prev_close = info.previous_close
        change = price - prev_close if prev_close else 0
        pct = (change / prev_close * 100) if prev_close else 0
    except Exception:
        price = prev_close = change = pct = None

    return {
        "symbol": symbol.upper(),
        "price": round(price, 4) if price else None,
        "previous_close": round(prev_close, 4) if prev_close else None,
        "change": round(change, 4) if change else None,
        "change_percent": round(pct, 2) if pct else None,
    }


def get_quotes(symbols: list[str]) -> list[dict]:
    """Return quotes for multiple symbols."""
    return [get_quote(s) for s in symbols]
