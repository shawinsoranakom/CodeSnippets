def __min_dist_top_down_dp(self, m: int, n: int) -> int:
    if m == -1:
        return n + 1
    elif n == -1:
        return m + 1
    elif self.dp[m][n] > -1:
        return self.dp[m][n]
    else:
        if self.word1[m] == self.word2[n]:
            self.dp[m][n] = self.__min_dist_top_down_dp(m - 1, n - 1)
        else:
            insert = self.__min_dist_top_down_dp(m, n - 1)
            delete = self.__min_dist_top_down_dp(m - 1, n)
            replace = self.__min_dist_top_down_dp(m - 1, n - 1)
            self.dp[m][n] = 1 + min(insert, delete, replace)

        return self.dp[m][n]
