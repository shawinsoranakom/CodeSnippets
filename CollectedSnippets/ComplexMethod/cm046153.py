def linear_assignment(cost_matrix: np.ndarray, thresh: float, use_lap: bool = True):
    """Perform linear assignment using either the scipy or lap.lapjv method.

    Args:
        cost_matrix (np.ndarray): The matrix containing cost values for assignments, with shape (N, M).
        thresh (float): Threshold for considering an assignment valid.
        use_lap (bool): Use lap.lapjv for the assignment. If False, scipy.optimize.linear_sum_assignment is used.

    Returns:
        matched_indices (list[list[int]] | np.ndarray): Matched indices of shape (K, 2), where K is the number of
            matches.
        unmatched_a (tuple | list | np.ndarray): Unmatched indices from the first set.
        unmatched_b (tuple | list | np.ndarray): Unmatched indices from the second set.

    Examples:
        >>> cost_matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> thresh = 5.0
        >>> matched_indices, unmatched_a, unmatched_b = linear_assignment(cost_matrix, thresh, use_lap=True)
    """
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), tuple(range(cost_matrix.shape[0])), tuple(range(cost_matrix.shape[1]))

    if use_lap:
        # Use lap.lapjv
        # https://github.com/gatagat/lap
        _, x, y = lap.lapjv(cost_matrix, extend_cost=True, cost_limit=thresh)
        matches = [[ix, mx] for ix, mx in enumerate(x) if mx >= 0]
        unmatched_a = np.where(x < 0)[0]
        unmatched_b = np.where(y < 0)[0]
    else:
        # Use scipy.optimize.linear_sum_assignment
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html
        x, y = scipy.optimize.linear_sum_assignment(cost_matrix)  # row x, col y
        matches = np.asarray([[x[i], y[i]] for i in range(len(x)) if cost_matrix[x[i], y[i]] <= thresh])
        if len(matches) == 0:
            unmatched_a = list(np.arange(cost_matrix.shape[0]))
            unmatched_b = list(np.arange(cost_matrix.shape[1]))
        else:
            unmatched_a = list(frozenset(np.arange(cost_matrix.shape[0])) - frozenset(matches[:, 0]))
            unmatched_b = list(frozenset(np.arange(cost_matrix.shape[1])) - frozenset(matches[:, 1]))

    return matches, unmatched_a, unmatched_b