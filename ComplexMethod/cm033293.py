def _split_integer_budget(magnitudes: List[float], budget: int) -> List[int]:
    """Split nonnegative integer budget across positive magnitudes (largest remainder)."""
    n = len(magnitudes)
    if n == 0 or budget == 0:
        return [0] * n
    total = sum(magnitudes)
    if total <= 0:
        base = budget // n
        rem = budget % n
        out = [base] * n
        for i in range(rem):
            out[i] += 1
        return out
    raw = [budget * m / total for m in magnitudes]
    floors = [int(math.floor(r)) for r in raw]
    remainder = budget - sum(floors)
    order = sorted(range(n), key=lambda i: raw[i] - floors[i], reverse=True)
    for j in range(remainder):
        floors[order[j]] += 1
    return floors