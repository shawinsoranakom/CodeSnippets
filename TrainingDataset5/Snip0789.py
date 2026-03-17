def naive_cut_rod_recursive(n: int, prices: list):
    _enforce_args(n, prices)
    if n == 0:
        return 0
    max_revue = float("-inf")
    for i in range(1, n + 1):
        max_revue = max(
            max_revue, prices[i - 1] + naive_cut_rod_recursive(n - i, prices)
        )

    return max_revue
