def prefix_sum(array: list[int], queries: list[tuple[int, int]]) -> list[int]:
    dp = [0] * len(array)
    dp[0] = array[0]
    for i in range(1, len(array)):
        dp[i] = dp[i - 1] + array[i]

    result = []
    for query in queries:
        left, right = query
        res = dp[right]
        if left > 0:
            res -= dp[left - 1]
        result.append(res)

    return result
