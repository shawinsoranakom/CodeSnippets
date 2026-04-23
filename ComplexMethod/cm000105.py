def calculate_each_score(
    data_lists: list[list[float]], weights: list[int]
) -> list[list[float]]:
    """
    >>> calculate_each_score([[20, 23, 22], [60, 90, 50], [2012, 2015, 2011]],
    ...                      [0, 0, 1])
    [[1.0, 0.0, 0.33333333333333337], [0.75, 0.0, 1.0], [0.25, 1.0, 0.0]]
    """
    score_lists: list[list[float]] = []
    for dlist, weight in zip(data_lists, weights):
        mind = min(dlist)
        maxd = max(dlist)

        score: list[float] = []
        # for weight 0 score is 1 - actual score
        if weight == 0:
            for item in dlist:
                try:
                    score.append(1 - ((item - mind) / (maxd - mind)))
                except ZeroDivisionError:
                    score.append(1)

        elif weight == 1:
            for item in dlist:
                try:
                    score.append((item - mind) / (maxd - mind))
                except ZeroDivisionError:
                    score.append(0)

        # weight not 0 or 1
        else:
            msg = f"Invalid weight of {weight:f} provided"
            raise ValueError(msg)

        score_lists.append(score)

    return score_lists