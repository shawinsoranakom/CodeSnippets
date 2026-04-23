async def test_prompt_logprobs_completion(
    client: openai.AsyncOpenAI, model_name: str, prompt_logprobs: int | None
):
    params: dict = {
        "prompt": ["A robot may not injure another robot", "My name is"],
        "model": model_name,
    }
    if prompt_logprobs is not None:
        params["extra_body"] = {"prompt_logprobs": prompt_logprobs}

    if prompt_logprobs is not None and prompt_logprobs < 0:
        with pytest.raises(BadRequestError):
            await client.completions.create(**params)
    else:
        completion = await client.completions.create(**params)
        if prompt_logprobs is not None:
            assert completion.choices[0].prompt_logprobs is not None
            assert len(completion.choices[0].prompt_logprobs) > 0

            assert completion.choices[1].prompt_logprobs is not None
            assert len(completion.choices[1].prompt_logprobs) > 0

        else:
            assert completion.choices[0].prompt_logprobs is None