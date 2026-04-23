def traceback(score: list[list[int]], query: str, subject: str) -> str:
    query = query.upper()
    subject = subject.upper()
    max_value = float("-inf")
    i_max = j_max = 0
    for i, row in enumerate(score):
        for j, value in enumerate(row):
            if value > max_value:
                max_value = value
                i_max, j_max = i, j
    i = i_max
    j = j_max
    align1 = ""
    align2 = ""
    gap = score_function("-", "-")
    if i == 0 or j == 0:
        return ""
    while i > 0 and j > 0:
        if score[i][j] == score[i - 1][j - 1] + score_function(
            query[i - 1], subject[j - 1]
        ):
            align1 = query[i - 1] + align1
            align2 = subject[j - 1] + align2
            i -= 1
            j -= 1
        elif score[i][j] == score[i - 1][j] + gap:
            align1 = query[i - 1] + align1
            align2 = f"-{align2}"
            i -= 1
        else:
            align1 = f"-{align1}"
            align2 = subject[j - 1] + align2
            j -= 1

    return f"{align1}\n{align2}"
