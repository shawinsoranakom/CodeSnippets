def test_create_logprobs_flat() -> None:
    prompt_logprobs = create_prompt_logprobs(flat_logprobs=True)
    assert isinstance(prompt_logprobs, FlatLogprobs)
    assert prompt_logprobs.start_indices == [0]
    assert prompt_logprobs.end_indices == [0]
    assert len(prompt_logprobs.token_ids) == 0
    assert len(prompt_logprobs.logprobs) == 0
    assert len(prompt_logprobs.ranks) == 0
    assert len(prompt_logprobs.decoded_tokens) == 0
    # Ensure first prompt position logprobs is empty
    assert len(prompt_logprobs) == 1
    assert prompt_logprobs[0] == dict()

    sample_logprobs = create_sample_logprobs(flat_logprobs=True)
    assert isinstance(sample_logprobs, FlatLogprobs)
    assert len(sample_logprobs.start_indices) == 0
    assert len(sample_logprobs.end_indices) == 0
    assert len(sample_logprobs.token_ids) == 0
    assert len(sample_logprobs.logprobs) == 0
    assert len(sample_logprobs.ranks) == 0
    assert len(sample_logprobs.decoded_tokens) == 0
    assert len(sample_logprobs) == 0