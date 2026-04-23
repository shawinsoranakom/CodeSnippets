async def test_integration_streaming_with_builtin_tools() -> None:
    """Test streaming responses with builtin tools."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = AsyncOpenAI(api_key=api_key)
    tools = ["web_search_preview"]  # type: ignore
    agent = OpenAIAgent(
        name="streaming_test",
        description="Test agent with streaming and builtin tools",
        client=client,
        model="gpt-4o",
        instructions="You are a helpful assistant with web search capabilities.",
        tools=tools,  # type: ignore
    )
    cancellation_token = CancellationToken()

    # Test streaming with builtin tools
    messages: list[Any] = []
    async for message in agent.on_messages_stream(
        [TextMessage(source="user", content="What are the latest news about renewable energy?")],
        cancellation_token,
    ):
        messages.append(message)

    # Verify we received some messages
    assert len(messages) > 0
    # Verify at least one message has content
    content_messages = [
        msg
        for msg in messages
        if hasattr(msg, "chat_message")
        and hasattr(msg.chat_message, "content")
        and getattr(msg.chat_message, "content", False)
    ]
    assert len(content_messages) > 0