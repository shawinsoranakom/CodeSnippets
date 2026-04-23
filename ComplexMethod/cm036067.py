def test_append_logprobs_for_next_position_flat() -> None:
    logprobs = create_sample_logprobs(flat_logprobs=True)
    append_logprobs_for_next_position(
        logprobs,
        token_ids=[1],
        logprobs=[0.1],
        decoded_tokens=["1"],
        rank=10,
        num_logprobs=-1,
    )
    append_logprobs_for_next_position(
        logprobs,
        token_ids=[2, 3],
        logprobs=[0.2, 0.3],
        decoded_tokens=["2", "3"],
        rank=11,
        num_logprobs=-1,
    )
    assert isinstance(logprobs, FlatLogprobs)
    assert logprobs.start_indices == [0, 1]
    assert logprobs.end_indices == [1, 3]
    assert logprobs.token_ids == [1, 2, 3]
    assert logprobs.logprobs == [0.1, 0.2, 0.3]
    assert logprobs.ranks == [10, 11, 1]
    assert logprobs.decoded_tokens == ["1", "2", "3"]