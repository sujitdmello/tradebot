"""Portfolio: balances and positions."""

import data_manager
import quotes


def get_balances() -> str:
    """Return formatted balance summary."""
    balances = data_manager.get_balances()
    return (
        f"Cash Balance:     ${balances['cash']:,.2f}\n"
        f"Non-Cash (Investments): ${balances['non_cash']:,.2f}\n"
        f"Total Portfolio Value:  ${balances['total']:,.2f}"
    )


def get_positions() -> str:
    """Return formatted list of all positions including cash."""
    positions = data_manager.get_positions()
    balances = data_manager.get_balances()

    lines = ["Symbol   | Type   | Quantity     | Avg Cost     | Current Price | Market Value",
             "---------|--------|------------- |------------- |-------------- |-------------"]
    total_market = 0.0
    for p in positions:
        mv = p["quantity"] * p["current_price"]
        total_market += mv
        lines.append(
            f"{p['symbol']:<8} | {p['type']:<6} | {p['quantity']:<12} | "
            f"${p['avg_cost']:>11,.4f} | ${p['current_price']:>12,.4f} | ${mv:>12,.2f}"
        )

    lines.append("")
    lines.append(f"Cash:                ${balances['cash']:>12,.2f}")
    lines.append(f"Invested (market):   ${total_market:>12,.2f}")
    lines.append(f"Total:               ${balances['cash'] + total_market:>12,.2f}")
    return "\n".join(lines)


def recalculate_balances():
    """Recalculate non-cash and total from current positions and refresh prices."""
    positions = data_manager.get_positions()
    balances = data_manager.get_balances()

    # Optionally refresh current prices
    for p in positions:
        try:
            q = quotes.get_quote(p["symbol"])
            if q["price"] is not None:
                p["current_price"] = q["price"]
        except Exception:
            pass

    non_cash = sum(p["quantity"] * p["current_price"] for p in positions)
    balances["non_cash"] = round(non_cash, 2)
    balances["total"] = round(balances["cash"] + non_cash, 2)

    data_manager.save_positions(positions)
    data_manager.save_balances(balances)
