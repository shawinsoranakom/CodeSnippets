async def test_anthropic_streaming(client: anthropic.AsyncAnthropic):
    resp = await client.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=1024,
        messages=[{"role": "user", "content": "how are you!"}],
        stream=True,
    )

    first_chunk = None
    chunk_count = 0
    async for chunk in resp:
        chunk_count += 1
        if first_chunk is None and chunk.type == "message_start":
            first_chunk = chunk
        print(chunk.model_dump_json())

    assert chunk_count > 0
    assert first_chunk is not None, "message_start chunk was never observed"
    assert first_chunk.message is not None, "first chunk should include message"
    assert first_chunk.message.usage is not None, (
        "first chunk should include usage stats"
    )
    assert first_chunk.message.usage.output_tokens == 0
    assert first_chunk.message.usage.input_tokens > 5