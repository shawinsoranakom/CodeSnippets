def traceback(score: list[list[int]], query: str, subject: str) -> str:
    r"""
    Perform traceback to find the optimal local alignment.
    Starts from the highest scoring cell in the matrix and traces back recursively
    until a 0 score is found. Returns the alignment strings.
    >>> traceback([[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 2], [0, 1, 0]], 'ACAC', 'CA')
    'CA\nCA'
    >>> traceback([[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 2], [0, 1, 0]], 'acac', 'ca')
    'CA\nCA'
    >>> traceback([[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 2], [0, 1, 0]], 'ACAC', 'ca')
    'CA\nCA'
    >>> traceback([[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 2], [0, 1, 0]], 'acac', 'CA')
    'CA\nCA'
    >>> traceback([[0, 0, 0]], 'ACAC', '')
    ''
    """
    # make both query and subject uppercase
    query = query.upper()
    subject = subject.upper()
    # find the indices of the maximum value in the score matrix
    max_value = float("-inf")
    i_max = j_max = 0
    for i, row in enumerate(score):
        for j, value in enumerate(row):
            if value > max_value:
                max_value = value
                i_max, j_max = i, j
    # Traceback logic to find optimal alignment
    i = i_max
    j = j_max
    align1 = ""
    align2 = ""
    gap = score_function("-", "-")
    # guard against empty query or subject
    if i == 0 or j == 0:
        return ""
    while i > 0 and j > 0:
        if score[i][j] == score[i - 1][j - 1] + score_function(
            query[i - 1], subject[j - 1]
        ):
            # optimal path is a diagonal take both letters
            align1 = query[i - 1] + align1
            align2 = subject[j - 1] + align2
            i -= 1
            j -= 1
        elif score[i][j] == score[i - 1][j] + gap:
            # optimal path is a vertical
            align1 = query[i - 1] + align1
            align2 = f"-{align2}"
            i -= 1
        else:
            # optimal path is a horizontal
            align1 = f"-{align1}"
            align2 = subject[j - 1] + align2
            j -= 1

    return f"{align1}\n{align2}"