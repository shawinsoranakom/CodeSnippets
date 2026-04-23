async def test_chat_completion_n_parameter_streaming(
    client: openai.AsyncOpenAI, model_name: str
):
    """Test that n parameter returns multiple choices for streaming requests."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]

    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=15,
        temperature=0.7,
        n=2,
        stream=True,
    )

    # Collect all chunks using defaultdict for dynamic handling
    chunks_by_index = defaultdict(list)
    async for chunk in stream:
        for choice in chunk.choices:
            if choice.delta.content:
                chunks_by_index[choice.index].append(choice.delta.content)

    # Verify both choices received content
    assert len(chunks_by_index[0]) > 0, "Choice 0 received no content chunks"
    assert len(chunks_by_index[1]) > 0, "Choice 1 received no content chunks"

    # Reconstruct full responses
    response_0 = "".join(chunks_by_index[0])
    response_1 = "".join(chunks_by_index[1])

    assert len(response_0) > 0, "Choice 0 has empty response"
    assert len(response_1) > 0, "Choice 1 has empty response"