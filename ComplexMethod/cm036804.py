async def test_completions_with_prompt_embeds(
    example_prompt_embeds,
    client_with_prompt_embeds: openai.AsyncOpenAI,
    model_name: str,
):
    encoded_embeds, encoded_embeds2 = example_prompt_embeds

    # Test case: Single prompt embeds input
    completion = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        extra_body={"prompt_embeds": encoded_embeds},
    )
    assert len(completion.choices[0].text) >= 1
    assert completion.choices[0].prompt_logprobs is None

    # Test case: batch completion with prompt_embeds
    completion = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        extra_body={"prompt_embeds": [encoded_embeds, encoded_embeds2]},
    )
    assert len(completion.choices) == 2
    assert len(completion.choices[0].text) >= 1
    assert len(completion.choices[1].text) >= 1

    # Test case: streaming with prompt_embeds
    single_completion = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        extra_body={"prompt_embeds": encoded_embeds},
    )
    single_output = single_completion.choices[0].text

    stream = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        extra_body={"prompt_embeds": encoded_embeds},
    )
    chunks = []
    finish_reason_count = 0
    async for chunk in stream:
        chunks.append(chunk.choices[0].text)
        if chunk.choices[0].finish_reason is not None:
            finish_reason_count += 1
    assert finish_reason_count == 1
    assert chunk.choices[0].finish_reason == "length"
    assert chunk.choices[0].text
    assert "".join(chunks) == single_output

    # Test case: batch streaming with prompt_embeds
    stream = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        extra_body={"prompt_embeds": [encoded_embeds, encoded_embeds2]},
    )
    chunks_stream_embeds: list[list[str]] = [[], []]
    finish_reason_count = 0
    async for chunk in stream:
        chunks_stream_embeds[chunk.choices[0].index].append(chunk.choices[0].text)
        if chunk.choices[0].finish_reason is not None:
            finish_reason_count += 1
    assert finish_reason_count == 2
    assert chunk.choices[0].finish_reason == "length"
    assert chunk.choices[0].text
    assert len(chunks_stream_embeds[0]) > 0
    assert len(chunks_stream_embeds[1]) > 0

    # Test case: mixed text and prompt_embeds
    completion_mixed = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt="This is a prompt",
        max_tokens=5,
        temperature=0.0,
        extra_body={"prompt_embeds": encoded_embeds},
    )
    assert len(completion.choices) == 2
    completion_text_only = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt="This is a prompt",
        max_tokens=5,
        temperature=0.0,
    )
    completion_embeds_only = await client_with_prompt_embeds.completions.create(
        model=model_name,
        prompt=None,
        max_tokens=5,
        temperature=0.0,
        extra_body={"prompt_embeds": encoded_embeds},
    )
    # Embeddings responses should be handled first
    assert completion_mixed.choices[0].text == completion_embeds_only.choices[0].text
    assert completion_mixed.choices[1].text == completion_text_only.choices[0].text