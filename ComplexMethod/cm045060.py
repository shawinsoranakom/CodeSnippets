async def test_tool_calling(agent: OpenAIAgent, cancellation_token: CancellationToken) -> None:
    """Test that enabling a built-in tool yields a tool-style JSON response via the Responses API."""
    message = TextMessage(source="user", content="What's the weather in New York?")

    all_messages: List[Any] = []
    async for msg in agent.on_messages_stream([message], cancellation_token):
        all_messages.append(msg)

    final_response = next((msg for msg in all_messages if hasattr(msg, "chat_message")), None)
    assert final_response is not None
    assert hasattr(final_response, "chat_message")
    response_msg = cast(Response, final_response)
    assert isinstance(response_msg.chat_message, TextMessage)
    assert response_msg.chat_message.content == '{"temperature": 72.5, "conditions": "sunny"}'