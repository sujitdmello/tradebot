"""Order management and trade execution."""

import threading
from datetime import datetime, timezone

import config
import data_manager
import insights
import quotes

# Keep references to background execution timers so they aren't GC'd
_pending_timers: list[threading.Timer] = []

# Callback set by the bot so the executor can print to the user
_notify_callback = None


def set_notify_callback(cb):
    global _notify_callback
    _notify_callback = cb


def _notify(msg: str):
    if _notify_callback:
        _notify_callback(msg)


# ---- Helpers ----------------------------------------------------------------

CRYPTO_SYMBOLS = {"BTC", "ETH", "SOL", "ADA", "DOGE", "XRP", "DOT", "AVAX",
                  "MATIC", "LINK", "SHIB"}


def _asset_type(symbol: str) -> str:
    return "crypto" if symbol.upper() in CRYPTO_SYMBOLS else "stock"


# ---- Trade functions exposed to the bot via function calling ----------------

def buy(symbol: str, quantity: float) -> str:
    """Place a buy order for a stock or crypto."""
    symbol = symbol.upper()
    asset_type = _asset_type(symbol)

    # Get live price
    q = quotes.get_quote(symbol)
    if q["price"] is None:
        return f"Could not fetch a price for {symbol}. Please check the symbol."
    price = q["price"]
    total_cost = round(price * quantity, 2)

    # Check cash
    balances = data_manager.get_balances()
    if total_cost > balances["cash"]:
        return (
            f"Insufficient cash. The order would cost ${total_cost:,.2f} "
            f"but you only have ${balances['cash']:,.2f} in cash. No margin orders allowed."
        )

    # Insight warning
    warning = ""
    try:
        warning = insights.check_trade_against_insights(symbol, "buy")
    except Exception:
        pass

    # Create open order
    order_id = data_manager.next_order_id()
    order = {
        "id": order_id,
        "symbol": symbol,
        "type": asset_type,
        "action": "buy",
        "quantity": quantity,
        "price": price,
        "total": total_cost,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    orders = data_manager.get_orders()
    orders.append(order)
    data_manager.save_orders(orders)

    # Schedule execution
    _schedule_execution(order_id)

    parts = [
        f"Buy order {order_id} placed: {quantity} {symbol} @ ${price:,.4f} = ${total_cost:,.2f}.",
        f"Status: OPEN — will execute shortly.",
    ]
    if warning:
        parts.append(f"\n⚠ Insight: {warning}")
    return "\n".join(parts)


def sell(symbol: str, quantity: float) -> str:
    """Place a sell order for a stock or crypto."""
    symbol = symbol.upper()
    asset_type = _asset_type(symbol)

    # Check position
    positions = data_manager.get_positions()
    pos = next((p for p in positions if p["symbol"] == symbol), None)
    if pos is None:
        return f"You do not own any {symbol}."
    if quantity > pos["quantity"]:
        return (
            f"You only own {pos['quantity']} of {symbol}. "
            f"Cannot sell {quantity}."
        )

    # Get live price
    q = quotes.get_quote(symbol)
    if q["price"] is None:
        return f"Could not fetch a price for {symbol}. Please check the symbol."
    price = q["price"]
    total_value = round(price * quantity, 2)

    # Insight warning
    warning = ""
    try:
        warning = insights.check_trade_against_insights(symbol, "sell")
    except Exception:
        pass

    # Create open order
    order_id = data_manager.next_order_id()
    order = {
        "id": order_id,
        "symbol": symbol,
        "type": asset_type,
        "action": "sell",
        "quantity": quantity,
        "price": price,
        "total": total_value,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    orders = data_manager.get_orders()
    orders.append(order)
    data_manager.save_orders(orders)

    # Schedule execution
    _schedule_execution(order_id)

    parts = [
        f"Sell order {order_id} placed: {quantity} {symbol} @ ${price:,.4f} = ${total_value:,.2f}.",
        f"Status: OPEN — will execute shortly.",
    ]
    if warning:
        parts.append(f"\n⚠ Insight: {warning}")
    return "\n".join(parts)


def cancel_order(order_id: str) -> str:
    """Cancel an open order."""
    order_id = order_id.upper()
    orders = data_manager.get_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None:
        return f"Order {order_id} not found."
    if order["status"] != "open":
        return f"Order {order_id} is already '{order['status']}' and cannot be cancelled."

    order["status"] = "cancelled"
    order["cancelled_at"] = datetime.now(timezone.utc).isoformat()
    data_manager.save_orders(orders)
    return f"Order {order_id} has been cancelled."


def get_order_status() -> str:
    """Return open, cancelled, and today-executed orders."""
    orders = data_manager.get_orders()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    open_orders = [o for o in orders if o["status"] == "open"]
    cancelled = [o for o in orders if o["status"] == "cancelled"]
    executed_today = [
        o for o in orders
        if o["status"] == "executed" and o.get("executed_at", "").startswith(today_str)
    ]

    lines = []
    lines.append("=== Open Orders ===")
    if open_orders:
        for o in open_orders:
            lines.append(f"  {o['id']} | {o['action'].upper()} {o['quantity']} {o['symbol']} @ ${o['price']:,.4f} | {o['status']}")
    else:
        lines.append("  None")

    lines.append("\n=== Cancelled Orders ===")
    if cancelled:
        for o in cancelled:
            lines.append(f"  {o['id']} | {o['action'].upper()} {o['quantity']} {o['symbol']} @ ${o['price']:,.4f} | cancelled at {o.get('cancelled_at','N/A')}")
    else:
        lines.append("  None")

    lines.append("\n=== Executed Today ===")
    if executed_today:
        for o in executed_today:
            lines.append(f"  {o['id']} | {o['action'].upper()} {o['quantity']} {o['symbol']} @ ${o['price']:,.4f} | executed at {o.get('executed_at','N/A')}")
    else:
        lines.append("  None")

    return "\n".join(lines)


def get_transaction_history() -> str:
    """Return all past orders."""
    orders = data_manager.get_orders()
    lines = ["ID      | Action | Symbol | Qty         | Price        | Total        | Status     | Date"]
    lines.append("-" * 110)
    for o in orders:
        date = o.get("executed_at") or o.get("cancelled_at") or o.get("created_at", "")
        lines.append(
            f"{o['id']:<7} | {o['action']:<6} | {o['symbol']:<6} | "
            f"{o['quantity']:<11} | ${o['price']:>10,.4f} | ${o['total']:>10,.2f} | "
            f"{o['status']:<10} | {date}"
        )
    return "\n".join(lines)


# ---- Background execution ---------------------------------------------------

def _schedule_execution(order_id: str):
    """Run execution in background after configured delay."""
    t = threading.Timer(config.ORDER_EXECUTION_DELAY, _execute_order, args=[order_id])
    t.daemon = True
    _pending_timers.append(t)
    t.start()


def _execute_order(order_id: str):
    """Execute the order: update balances, positions, and order status."""
    orders = data_manager.get_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if order is None or order["status"] != "open":
        return  # already cancelled or not found

    balances = data_manager.get_balances()
    positions = data_manager.get_positions()

    if order["action"] == "buy":
        # Re-check cash
        if order["total"] > balances["cash"]:
            _notify(f"⚠ Order {order_id} failed: insufficient cash at execution time.")
            order["status"] = "cancelled"
            order["cancelled_at"] = datetime.now(timezone.utc).isoformat()
            data_manager.save_orders(orders)
            return

        balances["cash"] = round(balances["cash"] - order["total"], 2)

        # Update or create position
        pos = next((p for p in positions if p["symbol"] == order["symbol"]), None)
        if pos:
            old_total = pos["quantity"] * pos["avg_cost"]
            new_total = order["quantity"] * order["price"]
            pos["quantity"] = round(pos["quantity"] + order["quantity"], 8)
            pos["avg_cost"] = round((old_total + new_total) / pos["quantity"], 4)
            pos["current_price"] = order["price"]
        else:
            positions.append({
                "symbol": order["symbol"],
                "name": order["symbol"],
                "type": order["type"],
                "quantity": order["quantity"],
                "avg_cost": order["price"],
                "current_price": order["price"],
            })

    elif order["action"] == "sell":
        # Re-check position
        pos = next((p for p in positions if p["symbol"] == order["symbol"]), None)
        if pos is None or order["quantity"] > pos["quantity"]:
            _notify(f"⚠ Order {order_id} failed: insufficient holdings at execution time.")
            order["status"] = "cancelled"
            order["cancelled_at"] = datetime.now(timezone.utc).isoformat()
            data_manager.save_orders(orders)
            return

        balances["cash"] = round(balances["cash"] + order["total"], 2)
        pos["quantity"] = round(pos["quantity"] - order["quantity"], 8)
        pos["current_price"] = order["price"]
        if pos["quantity"] <= 0:
            positions = [p for p in positions if p["symbol"] != order["symbol"]]

    # Recalculate totals
    non_cash = sum(p["quantity"] * p["current_price"] for p in positions)
    balances["non_cash"] = round(non_cash, 2)
    balances["total"] = round(balances["cash"] + non_cash, 2)
    balances["last_updated"] = datetime.now(timezone.utc).isoformat()

    order["status"] = "executed"
    order["executed_at"] = datetime.now(timezone.utc).isoformat()

    data_manager.save_orders(orders)
    data_manager.save_positions(positions)
    data_manager.save_balances(balances)

    _notify(
        f"✓ Order {order_id} executed: {order['action'].upper()} {order['quantity']} "
        f"{order['symbol']} @ ${order['price']:,.4f} (${order['total']:,.2f})."
    )
