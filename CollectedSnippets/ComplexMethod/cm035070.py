def cal_distance(word1, word2):
    m = len(word1)
    n = len(word2)
    if m * n == 0:
        return m + n
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            a = dp[i - 1][j] + 1
            b = dp[i][j - 1] + 1
            c = dp[i - 1][j - 1]
            if word1[i - 1] != word2[j - 1]:
                c += 1
            dp[i][j] = min(a, b, c)
    return dp[m][n]