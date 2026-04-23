def _most_frequent(array, extra_value, n_repeat):
    """Compute the most frequent value in a 1d array extended with
    [extra_value] * n_repeat, where extra_value is assumed to be not part
    of the array."""
    # Compute the most frequent value in array only
    if array.size > 0:
        if array.dtype == object:
            # scipy.stats.mode is slow with object dtype array.
            # Python Counter is more efficient
            counter = Counter(array)
            most_frequent_count = counter.most_common(1)[0][1]
            # tie breaking similarly to scipy.stats.mode
            most_frequent_value = _safe_min(
                [
                    value
                    for value, count in counter.items()
                    if count == most_frequent_count
                ]
            )
        else:
            mode = _mode(array)
            most_frequent_value = mode[0][0]
            most_frequent_count = mode[1][0]
    else:
        most_frequent_value = 0
        most_frequent_count = 0

    # Compare to array + [extra_value] * n_repeat
    if most_frequent_count == 0 and n_repeat == 0:
        return np.nan
    elif most_frequent_count < n_repeat:
        return extra_value
    elif most_frequent_count > n_repeat:
        return most_frequent_value
    elif most_frequent_count == n_repeat:
        # tie breaking similarly to scipy.stats.mode
        return _safe_min([most_frequent_value, extra_value])