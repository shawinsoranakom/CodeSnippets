def is_match(string: str, pattern: str) -> bool:
    dp = [[False] * (len(pattern) + 1) for _ in string + "1"]
    dp[0][0] = True
    for j, char in enumerate(pattern, 1):
        if char == "*":
            dp[0][j] = dp[0][j - 1]
    for i, s_char in enumerate(string, 1):
        for j, p_char in enumerate(pattern, 1):
            if p_char in (s_char, "?"):
                dp[i][j] = dp[i - 1][j - 1]
            elif pattern[j - 1] == "*":
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
    return dp[len(string)][len(pattern)]
