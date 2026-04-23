def test_flat_logprobs_append() -> None:
    logprobs = FlatLogprobs()
    logprobs.append(LOGPROBS_ONE_POSITION_0)
    logprobs.append(LOGPROBS_ONE_POSITION_1)
    assert logprobs.start_indices == [0, 1]
    assert logprobs.end_indices == [1, 3]
    assert logprobs.token_ids == [1, 2, 3]
    assert logprobs.logprobs == [0.1, 0.2, 0.3]
    assert logprobs.ranks == [10, 20, 30]
    assert logprobs.decoded_tokens == ["10", "20", "30"]

    logprobs.append(LOGPROBS_ONE_POSITION_2)
    assert logprobs.start_indices == [0, 1, 3]
    assert logprobs.end_indices == [1, 3, 6]
    assert logprobs.token_ids == [1, 2, 3, 4, 5, 6]
    assert logprobs.logprobs == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    assert logprobs.ranks == [10, 20, 30, 40, 50, 60]
    assert logprobs.decoded_tokens == ["10", "20", "30", "40", "50", "60"]