def smith_waterman(
    query: str,
    subject: str,
    match: int = 1,
    mismatch: int = -1,
    gap: int = -2,
) -> list[list[int]]:
    query = query.upper()
    subject = subject.upper()

    m = len(query)
    n = len(subject)
    score = [[0] * (n + 1) for _ in range(m + 1)]
    kwargs = {"match": match, "mismatch": mismatch, "gap": gap}

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match = score[i - 1][j - 1] + score_function(
                query[i - 1], subject[j - 1], **kwargs
            )
            delete = score[i - 1][j] + gap
            insert = score[i][j - 1] + gap

            score[i][j] = max(0, match, delete, insert)

    return score
