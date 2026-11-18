from ct import kpis


def test_stockout_rate():
    assert kpis.stockout_rate([0, 5, 0, 10]) == 0.5
    assert kpis.stockout_rate([]) == 0.0


def test_on_time_pct():
    assert kpis.on_time_pct([2, 5, 3], [3, 4, 3]) == 2 / 3
    assert kpis.on_time_pct([], []) is None


def test_days_of_inventory():
    assert kpis.days_of_inventory(100, 10) == 10
    assert kpis.days_of_inventory(100, 0) is None


def test_p90():
    assert kpis.p90([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 9.1
    assert kpis.p90([]) is None
