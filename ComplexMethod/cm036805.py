async def test_completions_with_logprobs_and_prompt_embeds(
    example_prompt_embeds,
    client_with_prompt_embeds: openai.AsyncOpenAI,
    logprobs_arg: int,
    model_name: str,
):
    encoded_embeds, encoded_embeds2 = example_prompt_embeds

    # Test case: Logprobs using prompt_embeds
    completion = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        echo=False,
        logprobs=logprobs_arg,
        extra_body={"prompt_embeds": encoded_embeds},
    )

    logprobs = completion.choices[0].logprobs
    assert logprobs is not None
    assert len(logprobs.text_offset) == 5
    assert len(logprobs.token_logprobs) == 5
    assert len(logprobs.top_logprobs) == 5
    for top_logprobs in logprobs.top_logprobs[1:]:
        assert max(logprobs_arg, 1) <= len(top_logprobs) <= logprobs_arg + 1
    assert len(logprobs.tokens) == 5

    # Test case: Log probs with batch completion and prompt_embeds
    completion = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        echo=False,
        logprobs=logprobs_arg,
        extra_body={"prompt_embeds": [encoded_embeds, encoded_embeds2]},
    )

    assert len(completion.choices) == 2
    for choice in completion.choices:
        logprobs = choice.logprobs
        assert logprobs is not None
        assert len(logprobs.text_offset) == 5
        assert len(logprobs.token_logprobs) == 5
        assert len(logprobs.top_logprobs) == 5
        for top_logprobs in logprobs.top_logprobs[1:]:
            assert max(logprobs_arg, 1) <= len(top_logprobs) <= logprobs_arg + 1
        assert len(logprobs.tokens) == 5