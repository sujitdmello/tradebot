"""Thin JSON persistence layer for all data files."""

import json
import os
import threading

import config

_lock = threading.Lock()


def _path(filename: str) -> str:
    return os.path.join(config.DATA_DIR, filename)


def load(filename: str):
    with _lock:
        with open(_path(filename), "r", encoding="utf-8") as f:
            return json.load(f)


def save(filename: str, data):
    with _lock:
        with open(_path(filename), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


# --- User helpers ---

def get_username() -> str | None:
    return load("user.json").get("username")


def set_username(name: str):
    data = load("user.json")
    data["username"] = name
    save("user.json", data)


# --- Balances helpers ---

def get_balances() -> dict:
    return load("balances.json")


def save_balances(balances: dict):
    save("balances.json", balances)


# --- Positions helpers ---

def get_positions() -> list[dict]:
    return load("positions.json")


def save_positions(positions: list[dict]):
    save("positions.json", positions)


# --- Orders helpers ---

def get_orders() -> list[dict]:
    return load("orders.json")


def save_orders(orders: list[dict]):
    save("orders.json", orders)


def next_order_id() -> str:
    orders = get_orders()
    max_num = 0
    for o in orders:
        try:
            num = int(o["id"].replace("ORD", ""))
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    return f"ORD{max_num + 1:03d}"
