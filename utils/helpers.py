from time import time
import math


def round_step_size(quantity: float, step_size: float) -> float:
    """
    Rounds a number to the nearest multiple of step_size, rounding down.
    """
    if step_size <= 0:
        return quantity
    # Use simple math to floor to step size
    # e.g. qty=0.123, step=0.01 -> 0.12
    # e.g. qty=105, step=10 -> 100
    precision = int(round(-math.log(step_size, 10), 0))
    # Avoid float issues by using formatted string for final rounding if needed, 
    # but floor logic is safer:
    steps = math.floor(quantity / step_size)
    result = steps * step_size
    # Fix floating point artifacts like 300.000000000004
    if precision >= 0:
        return round(result, precision)
    return result


def format_price(price: float) -> str:
    return f"${price:,.2f}"


def format_qty(qty: float) -> str:
    return f"{qty:.4f}"


def format_pnl(pnl: float, percent: float) -> str:
    sign = "+" if pnl >= 0 else "-"
    return f"{sign}${abs(pnl):,.2f} ({percent:.2f}%)"


def calculate_pnl_percent(entry: float, current: float, side: str) -> float:
    if entry <= 0:
        return 0.0
    if side.lower() == "buy":
        return (current - entry) / entry * 100
    return (entry - current) / entry * 100


def timestamp_ms() -> int:
    return int(time() * 1000)
