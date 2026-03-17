def matrix_chain_multiply(arr: list[int]) -> int:
    if len(arr) < 2:
        return 0
    n = len(arr)
    dp = [[maxsize for j in range(n)] for i in range(n)]
    for i in range(n - 1, 0, -1):
        for j in range(i, n):
            if i == j:
                dp[i][j] = 0
                continue
            for k in range(i, j):
                dp[i][j] = min(
                    dp[i][j], dp[i][k] + dp[k + 1][j] + arr[i - 1] * arr[k] * arr[j]
                )

    return dp[1][n - 1]
