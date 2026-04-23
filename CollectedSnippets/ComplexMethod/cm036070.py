def test_flat_logprobs_access() -> None:
    logprobs = FlatLogprobs()
    logprobs.extend(
        [LOGPROBS_ONE_POSITION_1, LOGPROBS_ONE_POSITION_2, LOGPROBS_ONE_POSITION_0]
    )
    assert logprobs.start_indices == [0, 2, 5]
    assert logprobs.end_indices == [2, 5, 6]
    assert logprobs.token_ids == [2, 3, 4, 5, 6, 1]
    assert logprobs.logprobs == [0.2, 0.3, 0.4, 0.5, 0.6, 0.1]
    assert logprobs.ranks == [20, 30, 40, 50, 60, 10]
    assert logprobs.decoded_tokens == ["20", "30", "40", "50", "60", "10"]

    # Test __len__
    assert len(logprobs) == 3

    # Test __iter__
    for actual_logprobs, expected_logprobs in zip(
        logprobs,
        [LOGPROBS_ONE_POSITION_1, LOGPROBS_ONE_POSITION_2, LOGPROBS_ONE_POSITION_0],
    ):
        assert actual_logprobs == expected_logprobs

    # Test __getitem__ : single item
    assert logprobs[0] == LOGPROBS_ONE_POSITION_1
    assert logprobs[1] == LOGPROBS_ONE_POSITION_2
    assert logprobs[2] == LOGPROBS_ONE_POSITION_0

    # Test __getitem__ : slice
    logprobs02 = logprobs[:2]
    assert len(logprobs02) == 2
    assert logprobs02[0] == LOGPROBS_ONE_POSITION_1
    assert logprobs02[1] == LOGPROBS_ONE_POSITION_2
    assert logprobs02.start_indices == [0, 2]
    assert logprobs02.end_indices == [2, 5]
    assert logprobs02.token_ids == [2, 3, 4, 5, 6]
    assert logprobs02.logprobs == [0.2, 0.3, 0.4, 0.5, 0.6]
    assert logprobs02.ranks == [20, 30, 40, 50, 60]
    assert logprobs02.decoded_tokens == ["20", "30", "40", "50", "60"]
    logprobs_last2 = logprobs[-2:]
    assert len(logprobs_last2) == 2
    assert logprobs_last2[0] == LOGPROBS_ONE_POSITION_2
    assert logprobs_last2[1] == LOGPROBS_ONE_POSITION_0
    assert logprobs_last2.start_indices == [0, 3]
    assert logprobs_last2.end_indices == [3, 4]
    assert logprobs_last2.token_ids == [4, 5, 6, 1]
    assert logprobs_last2.logprobs == [0.4, 0.5, 0.6, 0.1]
    assert logprobs_last2.ranks == [40, 50, 60, 10]
    assert logprobs_last2.decoded_tokens == ["40", "50", "60", "10"]