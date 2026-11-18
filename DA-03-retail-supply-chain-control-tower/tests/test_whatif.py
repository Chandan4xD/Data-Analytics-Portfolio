import pandas as pd

from ct import whatif


def test_units_short():
    assert whatif.units_short(on_hand=10, daily_demand=2, lead_days=3, delay_days=0) == 0
    assert whatif.units_short(on_hand=10, daily_demand=2, lead_days=3, delay_days=4) == 4


def test_scenarios_grow_with_delay():
    products = pd.DataFrame({"supplier_id": ["S1", "S1"], "on_hand": [10, 4], "daily_demand": [1.0, 1.0],
                             "lead_days": [3, 3], "unit_price": [10.0, 20.0]})
    s = whatif.build_scenarios(products, max_delay=10)
    assert len(s) == 11
    assert s["products_at_risk"].is_monotonic_increasing
    assert s.loc[s.delay_days == 0, "products_at_risk"].item() == 0
    assert s.loc[s.delay_days == 10, "products_at_risk"].item() == 2
