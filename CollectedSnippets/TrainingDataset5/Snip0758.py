def min_dist_bottom_up(self, word1: str, word2: str) -> int:
    self.word1 = word1
    self.word2 = word2
    m = len(word1)
    n = len(word2)
    self.dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]

    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0: 
                self.dp[i][j] = j
            elif j == 0: 
                self.dp[i][j] = i
            elif word1[i - 1] == word2[j - 1]: 
                self.dp[i][j] = self.dp[i - 1][j - 1]
            else:
                insert = self.dp[i][j - 1]
                delete = self.dp[i - 1][j]
                replace = self.dp[i - 1][j - 1]
                self.dp[i][j] = 1 + min(insert, delete, replace)
    return self.dp[m][n]
