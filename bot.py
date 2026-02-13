"""TradeBot – Azure OpenAI powered chat bot with function-calling."""

import json
from openai import AzureOpenAI

import config
import data_manager
import insights
import portfolio
import quotes
import trading

# ---- Azure OpenAI client ----------------------------------------------------

_client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
)

# ---- Tool definitions for function calling -----------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_balances",
            "description": "Get the user's account balances including cash, non-cash (investments), and total portfolio value.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_positions",
            "description": "Get all current stock and crypto positions/holdings the user owns, including cash.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transaction_history",
            "description": "Get the full history of all past transactions (buy, sell, cancel).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buy",
            "description": "Place a buy order for a stock or cryptocurrency. The order starts as 'open' and executes after a short delay.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The ticker symbol to buy (e.g. AAPL, BTC, ETH).",
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The number of shares or units to buy.",
                    },
                },
                "required": ["symbol", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sell",
            "description": "Place a sell order for a stock or cryptocurrency. The order starts as 'open' and executes after a short delay.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The ticker symbol to sell (e.g. AAPL, BTC, ETH).",
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The number of shares or units to sell.",
                    },
                },
                "required": ["symbol", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "Cancel an open order by its order ID. Only open orders can be cancelled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to cancel (e.g. ORD024).",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get the status of all open orders, cancelled orders, and orders executed today.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quote",
            "description": "Get the current price quote for a stock or cryptocurrency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The ticker symbol (e.g. AAPL, MSFT, BTC, ETH).",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_insights",
            "description": "Get AI-generated insights and analysis for a stock or cryptocurrency based on recent news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The ticker symbol to analyze (e.g. AAPL, BTC).",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_username",
            "description": "Change the user's display name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The new name for the user.",
                    },
                },
                "required": ["name"],
            },
        },
    },
]

# ---- Function dispatch -------------------------------------------------------

def _dispatch(name: str, args: dict) -> str:
    """Call the appropriate function and return the string result."""
    if name == "get_balances":
        return portfolio.get_balances()
    elif name == "get_positions":
        return portfolio.get_positions()
    elif name == "get_transaction_history":
        return trading.get_transaction_history()
    elif name == "buy":
        return trading.buy(args["symbol"], float(args["quantity"]))
    elif name == "sell":
        return trading.sell(args["symbol"], float(args["quantity"]))
    elif name == "cancel_order":
        return trading.cancel_order(args["order_id"])
    elif name == "get_order_status":
        return trading.get_order_status()
    elif name == "get_quote":
        q = quotes.get_quote(args["symbol"])
        if q["price"] is None:
            return f"Could not fetch quote for {args['symbol']}. Check the symbol."
        return (
            f"{q['symbol']}: ${q['price']:,.4f}  "
            f"(prev close ${q['previous_close']:,.4f}, "
            f"change {q['change']:+,.4f} / {q['change_percent']:+.2f}%)"
        )
    elif name == "get_insights":
        return insights.get_insights(args["symbol"])
    elif name == "change_username":
        data_manager.set_username(args["name"])
        return f"Username changed to {args['name']}."
    else:
        return f"Unknown function: {name}"


# ---- Bot class ---------------------------------------------------------------

class TradeBot:
    def __init__(self):
        self.username: str | None = data_manager.get_username()
        self.messages: list[dict] = []
        self._init_system_prompt()
        # Wire up the order-execution notification so it can print to console
        trading.set_notify_callback(self._on_order_notification)
        self._pending_notifications: list[str] = []

    def _init_system_prompt(self):
        name_part = f"The user's name is {self.username}. " if self.username else ""
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are TradeBot, a friendly and knowledgeable stock and crypto trading assistant. "
                    f"{name_part}"
                    "You help the user check balances, view positions, trade stocks and crypto, "
                    "check quotes, review order status, see transaction history, and get insights. "
                    "Always refer to the user by name if known. "
                    "When the user wants to trade, use the buy or sell functions. "
                    "Before confirming a trade, call get_insights to check current sentiment "
                    "and warn the user if the trade goes against the insights. "
                    "Use get_quote to show current prices when relevant. "
                    "Be concise, helpful, and professional. Format data clearly."
                ),
            }
        ]

    def _on_order_notification(self, msg: str):
        self._pending_notifications.append(msg)

    def get_pending_notifications(self) -> list[str]:
        notes = list(self._pending_notifications)
        self._pending_notifications.clear()
        return notes

    def set_username(self, name: str):
        self.username = name
        data_manager.set_username(name)
        self._init_system_prompt()

    def chat(self, user_input: str) -> str:
        """Process a user message and return the bot's response."""
        self.messages.append({"role": "user", "content": user_input})

        while True:
            response = _client.chat.completions.create(
                model=config.AZURE_OPENAI_DEPLOYMENT,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.1,
            )
            msg = response.choices[0].message

            # If no tool calls, return the text response
            if not msg.tool_calls:
                assistant_text = msg.content or ""
                self.messages.append({"role": "assistant", "content": assistant_text})
                return assistant_text

            # Process tool calls
            self.messages.append(msg)

            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                result = _dispatch(fn_name, fn_args)

                # If username was changed via function call, update locally
                if fn_name == "change_username":
                    self.username = fn_args.get("name", self.username)
                    self._init_system_prompt()

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            # Loop back so the model can produce a final text answer
