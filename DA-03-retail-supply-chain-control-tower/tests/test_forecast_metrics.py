from ct.forecast import mape, wape


def test_mape_ignores_zero_actuals():
    assert mape([10, 0, 20], [8, 5, 20]) == (0.2 + 0.0) / 2


def test_wape():
    assert wape([10, 10], [8, 12]) == 0.2
    assert wape([0, 0], [1, 1]) is None
