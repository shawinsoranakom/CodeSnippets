def test_flat_logprobs_extend() -> None:
    logprobs = FlatLogprobs()
    # Extend with list[LogprobsOnePosition]
    logprobs.extend([LOGPROBS_ONE_POSITION_2, LOGPROBS_ONE_POSITION_0])
    assert logprobs.start_indices == [0, 3]
    assert logprobs.end_indices == [3, 4]
    assert logprobs.token_ids == [4, 5, 6, 1]
    assert logprobs.logprobs == [0.4, 0.5, 0.6, 0.1]
    assert logprobs.ranks == [40, 50, 60, 10]
    assert logprobs.decoded_tokens == ["40", "50", "60", "10"]

    other_logprobs = FlatLogprobs()
    other_logprobs.extend([LOGPROBS_ONE_POSITION_1, LOGPROBS_ONE_POSITION_0])
    # Extend with another FlatLogprobs
    logprobs.extend(other_logprobs)
    assert logprobs.start_indices == [0, 3, 4, 6]
    assert logprobs.end_indices == [3, 4, 6, 7]
    assert logprobs.token_ids == [4, 5, 6, 1, 2, 3, 1]
    assert logprobs.logprobs == [0.4, 0.5, 0.6, 0.1, 0.2, 0.3, 0.1]
    assert logprobs.ranks == [40, 50, 60, 10, 20, 30, 10]
    assert logprobs.decoded_tokens == ["40", "50", "60", "10", "20", "30", "10"]