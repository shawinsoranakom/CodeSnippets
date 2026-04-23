def test_detokenize_false(llm):
    """Check that detokenize=False option works."""

    output = llm.generate(PROMPT, SamplingParams(detokenize=False))
    assert len(output[0].outputs[0].token_ids) > 0
    assert len(output[0].outputs[0].text) == 0

    output = llm.generate(
        PROMPT, SamplingParams(detokenize=False, logprobs=3, prompt_logprobs=3)
    )
    assert len(output[0].outputs[0].token_ids) > 0
    assert len(output[0].outputs[0].text) == 0

    prompt_logprobs = output[0].prompt_logprobs
    sampled_logprobs = output[0].outputs[0].logprobs
    assert len(prompt_logprobs) > 1
    assert len(sampled_logprobs) > 1
    for all_logprobs in (prompt_logprobs[1:], sampled_logprobs):
        for logprobs in all_logprobs:
            assert 3 <= len(logprobs) <= 4
            assert all(lp.decoded_token is None for lp in logprobs.values())