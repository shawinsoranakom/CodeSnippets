def abbr(a: str, b: str) -> bool:
    """
    >>> abbr("daBcd", "ABC")
    True
    >>> abbr("dBcd", "ABC")
    False
    """
    n = len(a)
    m = len(b)
    dp = [[False for _ in range(m + 1)] for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(n):
        for j in range(m + 1):
            if dp[i][j]:
                if j < m and a[i].upper() == b[j]:
                    dp[i + 1][j + 1] = True
                if a[i].islower():
                    dp[i + 1][j] = True
    return dp[n][m]