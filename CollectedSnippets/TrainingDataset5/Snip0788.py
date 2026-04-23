def dp_match(text: str, pattern: str) -> bool:
    m = len(text)
    n = len(pattern)
    dp = [[False for _ in range(n + 1)] for _ in range(m + 1)]
    dp[0][0] = True

    for j in range(1, n + 1):
        dp[0][j] = pattern[j - 1] == "*" and dp[0][j - 2]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pattern[j - 1] in {".", text[i - 1]}:
                dp[i][j] = dp[i - 1][j - 1]
            elif pattern[j - 1] == "*":
                dp[i][j] = dp[i][j - 2]
                if pattern[j - 2] in {".", text[i - 1]}:
                    dp[i][j] |= dp[i - 1][j]
            else:
                dp[i][j] = False

    return dp[m][n]
