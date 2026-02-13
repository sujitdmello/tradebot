#!/usr/bin/env python3
"""TradeBot – main entry point."""

import sys

from bot import TradeBot


def main():
    print("=" * 60)
    print("  Welcome to TradeBot – Your Trading Assistant")
    print("=" * 60)

    bot = TradeBot()

    # Ask for username if not set
    if not bot.username:
        name = input("\nWhat should I call you? > ").strip()
        if name:
            bot.set_username(name)
            print(f"\nGreat to meet you, {name}! Let's get trading.\n")
        else:
            print("\nNo name provided — I'll just call you 'Trader'.\n")
            bot.set_username("Trader")
    else:
        print(f"\nWelcome back, {bot.username}!\n")

    print("Type your request in plain English (e.g. 'show my balances', ")
    print("'buy 10 AAPL', 'get a quote for BTC', 'show insights for TSLA').")
    print("Type 'quit' or 'exit' to leave.\n")

    while True:
        # Print any background order-execution notifications
        for note in bot.get_pending_notifications():
            print(f"\n[TradeBot] {note}")

        try:
            user_input = input(f"{bot.username} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print(f"\nGoodbye, {bot.username}! Happy trading.")
            break

        try:
            response = bot.chat(user_input)
            print(f"\nTradeBot > {response}\n")
        except Exception as e:
            print(f"\n[Error] {e}\n")


if __name__ == "__main__":
    main()
