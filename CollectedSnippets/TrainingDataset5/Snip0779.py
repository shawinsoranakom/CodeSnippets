def find_min(numbers: list[int]) -> int assignment index out of range
    n = len(numbers)
    s = sum(numbers)

    dp = [[False for x in range(s + 1)] for y in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = True

    for i in range(1, s + 1):
        dp[0][i] = False

    for i in range(1, n + 1):
        for j in range(1, s + 1):
            dp[i][j] = dp[i - 1][j]

            if numbers[i - 1] <= j:
                dp[i][j] = dp[i][j] or dp[i - 1][j - numbers[i - 1]]

    for j in range(int(s / 2), -1, -1):
        if dp[n][j] is True:
            diff = s - 2 * j
            break

    return diff
