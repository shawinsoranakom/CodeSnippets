def _top_down_cut_rod_recursive(n: int, prices: list, max_rev: list):
    if max_rev[n] >= 0:
        return max_rev[n]
    elif n == 0:
        return 0
    else:
        max_revenue = float("-inf")
        for i in range(1, n + 1):
            max_revenue = max(
                max_revenue,
                prices[i - 1] + _top_down_cut_rod_recursive(n - i, prices, max_rev),
            )

        max_rev[n] = max_revenue

    return max_rev[n]
