async def test_sk_chat_completion_stream_without_tools(
    sk_client: AzureChatCompletion, caplog: pytest.LogCaptureFixture
) -> None:
    # Create adapter and kernel
    adapter = SKChatCompletionAdapter(sk_client)
    kernel = Kernel(memory=NullMemory())

    # Test messages
    messages: list[LLMMessage] = [
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Say hello!", source="user"),
    ]

    # Call create_stream without tools
    response_chunks: list[CreateResult | str] = []
    with caplog.at_level(logging.INFO):
        async for chunk in adapter.create_stream(messages=messages, extra_create_args={"kernel": kernel}):
            response_chunks.append(chunk)

        assert "LLMStreamStart" in caplog.text
        assert "LLMStreamEnd" in caplog.text

        # Verify response
        assert len(response_chunks) > 0
        # All chunks except last should be strings
        for chunk in response_chunks[:-1]:
            assert isinstance(chunk, str)

        # Final chunk should be CreateResult
        final_chunk = response_chunks[-1]
        assert isinstance(final_chunk, CreateResult)
        assert isinstance(final_chunk.content, str)
        assert final_chunk.finish_reason == "stop"
        assert final_chunk.usage.prompt_tokens >= 0
        assert final_chunk.usage.completion_tokens >= 0
        assert not final_chunk.cached
        assert final_chunk.content in caplog.text