async def test_chat_completion_stream_options(
    client: openai.AsyncOpenAI, model_name: str
):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]

    # Test stream=True, stream_options={"include_usage": False}
    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=10,
        temperature=0.0,
        stream=True,
        stream_options={"include_usage": False},
    )
    async for chunk in stream:
        assert chunk.usage is None

    # Test stream=True, stream_options={"include_usage": True,
    #                                   "continuous_usage_stats": False}}
    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=10,
        temperature=0.0,
        stream=True,
        stream_options={"include_usage": True, "continuous_usage_stats": False},
    )

    async for chunk in stream:
        if chunk.choices[0].finish_reason is None:
            assert chunk.usage is None
        else:
            assert chunk.usage is None
            final_chunk = await anext(stream)
            assert final_chunk.usage is not None
            assert final_chunk.usage.prompt_tokens > 0
            assert final_chunk.usage.completion_tokens > 0
            assert final_chunk.usage.total_tokens == (
                final_chunk.usage.prompt_tokens + final_chunk.usage.completion_tokens
            )
            assert final_chunk.choices == []

    # Test stream=False, stream_options={"include_usage": None}
    with pytest.raises(BadRequestError):
        await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=10,
            temperature=0.0,
            stream=False,
            stream_options={"include_usage": None},
        )

    # Test stream=False, stream_options={"include_usage": True}
    with pytest.raises(BadRequestError):
        await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=10,
            temperature=0.0,
            stream=False,
            stream_options={"include_usage": True},
        )

    # Test stream=True, stream_options={"include_usage": True,
    #                           "continuous_usage_stats": True}
    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=10,
        extra_body=dict(min_tokens=10),
        temperature=0.0,
        stream=True,
        stream_options={
            "include_usage": True,
            "continuous_usage_stats": True,
        },
    )
    last_completion_tokens = 0
    async for chunk in stream:
        assert chunk.usage.prompt_tokens >= 0
        assert (
            last_completion_tokens == 0
            or chunk.usage.completion_tokens > last_completion_tokens
            or (
                not chunk.choices
                and chunk.usage.completion_tokens == last_completion_tokens
            )
        )
        assert chunk.usage.total_tokens == (
            chunk.usage.prompt_tokens + chunk.usage.completion_tokens
        )
        last_completion_tokens = chunk.usage.completion_tokens

    assert last_completion_tokens == 10