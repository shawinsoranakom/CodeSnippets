def longest_common_substring(text1: str, text2: str) -> str:
    if not (isinstance(text1, str) and isinstance(text2, str)):
        raise ValueError("longest_common_substring() takes two strings for inputs")

    if not text1 or not text2:
        return ""

    text1_length = len(text1)
    text2_length = len(text2)

    dp = [[0] * (text2_length + 1) for _ in range(text1_length + 1)]
    end_pos = 0
    max_length = 0

    for i in range(1, text1_length + 1):
        for j in range(1, text2_length + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = 1 + dp[i - 1][j - 1]
                if dp[i][j] > max_length:
                    end_pos = i
                    max_length = dp[i][j]

    return text1[end_pos - max_length : end_pos]
