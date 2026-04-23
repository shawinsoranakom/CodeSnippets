async def test_sk_chat_completion_stream_with_tools(sk_client: AzureChatCompletion) -> None:
    # Create adapter and kernel
    adapter = SKChatCompletionAdapter(sk_client)
    kernel = Kernel(memory=NullMemory())

    # Create calculator tool
    tool = CalculatorTool()

    # Test messages
    messages: list[LLMMessage] = [
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="What is 2 + 2?", source="user"),
    ]

    # Call create_stream with tool
    response_chunks: list[CreateResult | str] = []
    async for chunk in adapter.create_stream(messages=messages, tools=[tool], extra_create_args={"kernel": kernel}):
        response_chunks.append(chunk)

    # Verify response
    assert len(response_chunks) > 0
    final_chunk = response_chunks[-1]
    assert isinstance(final_chunk, CreateResult)
    assert isinstance(final_chunk.content, list)  # Function calls
    assert final_chunk.finish_reason == "function_calls"
    assert final_chunk.usage.prompt_tokens >= 0
    assert final_chunk.usage.completion_tokens >= 0
    assert not final_chunk.cached