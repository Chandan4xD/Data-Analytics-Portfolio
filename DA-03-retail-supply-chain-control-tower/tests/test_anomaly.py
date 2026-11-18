from ct import anomaly


def test_needs_enough_history():
    z, mu, sd, flagged = anomaly.detect([1, 1, 1], 10, min_points=7)
    assert z is None and not flagged


def test_flags_a_spike():
    history = [1.0, 1.2, 0.9, 1.1, 1.0, 1.3, 0.8, 1.0, 1.1, 0.9]
    z, mu, sd, flagged = anomaly.detect(history, 7.0)
    assert flagged and z > 3


def test_normal_value_not_flagged():
    history = [1.0, 1.2, 0.9, 1.1, 1.0, 1.3, 0.8, 1.0, 1.1, 0.9]
    assert not anomaly.detect(history, 1.1)[3]


def test_flat_baseline_does_not_divide_by_zero():
    z, mu, sd, flagged = anomaly.detect([2.0] * 10, 2.0)
    assert z == 0 and not flagged
    assert anomaly.detect([2.0] * 10, 5.0)[3]


def test_min_delta_suppresses_tiny_changes():
    history = [0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1]
    assert anomaly.detect(history, 1.0, min_delta=0.0)[3]
    assert not anomaly.detect(history, 1.0, min_delta=2.0)[3]
    assert anomaly.detect(history, 7.0, min_delta=2.0)[3]
