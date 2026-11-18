import numpy as np


def stockout_rate(on_hand):
    vals = list(on_hand)
    if not vals:
        return 0.0
    return sum(1 for x in vals if x <= 0) / len(vals)


def on_time_pct(real_days, scheduled_days):
    pairs = list(zip(real_days, scheduled_days))
    if not pairs:
        return None
    return sum(1 for r, s in pairs if r <= s) / len(pairs)


def days_of_inventory(total_on_hand, avg_daily_demand):
    if avg_daily_demand is None or avg_daily_demand <= 0:
        return None
    return total_on_hand / avg_daily_demand


def p90(values):
    vals = [v for v in values if v is not None]
    return float(np.percentile(vals, 90)) if vals else None


def mean_or_none(values):
    vals = [v for v in values if v is not None]
    return float(np.mean(vals)) if vals else None
