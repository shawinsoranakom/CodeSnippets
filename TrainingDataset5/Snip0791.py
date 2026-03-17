def bottom_up_cut_rod(n: int, prices: list):
    _enforce_args(n, prices)

    max_rev = [float("-inf") for _ in range(n + 1)]
    max_rev[0] = 0

    for i in range(1, n + 1):
        max_revenue_i = max_rev[i]
        for j in range(1, i + 1):
            max_revenue_i = max(max_revenue_i, prices[j - 1] + max_rev[i - j])

        max_rev[i] = max_revenue_i

    return max_rev[n]
