def check_sequence_repetition(
    token_ids: Sequence[int],
    params: RepetitionDetectionParams,
) -> bool:
    """Check if a sequence of token IDs has a repetition pattern.
    Args:
        token_ids: List of token IDs
        params: Repetition detection parameters.
    Returns:
        True if a repetition pattern is found, False otherwise.
    """
    max_pattern_size = params.max_pattern_size
    min_pattern_size = params.min_pattern_size
    min_count = params.min_count

    if min_pattern_size <= 0:
        min_pattern_size = 1

    if max_pattern_size <= 0 or min_count < 2 or min_pattern_size > max_pattern_size:
        return False

    for pattern_len in range(
        min_pattern_size,
        max_pattern_size + 1,
    ):
        if pattern_len * min_count > len(token_ids):
            return False

        if _has_repeating_pattern(token_ids, pattern_len, min_count):
            return True

    return False