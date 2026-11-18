from statistics import mean, pstdev


def detect(history, value, threshold=3.0, window=14, min_points=7, min_delta=0.0):
    h = [x for x in list(history)[-window:] if x is not None]
    if value is None or len(h) < min_points:
        return None, None, None, False
    mu = mean(h)
    sd = max(pstdev(h), 0.05 * abs(mu), 1e-3)
    z = (value - mu) / sd
    return z, mu, sd, abs(z) >= threshold and abs(value - mu) >= min_delta
