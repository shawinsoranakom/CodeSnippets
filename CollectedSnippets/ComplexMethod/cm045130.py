async def test_system_message_merge_with_continuous_system_messages_models() -> None:
    """Tests that system messages are merged correctly for Gemini models."""
    # Create a mock client
    mock_client = MagicMock()
    client = BaseOpenAIChatCompletionClient(
        client=mock_client,
        create_args={"model": "gemini-1.5-flash"},
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
            "multiple_system_messages": False,
        },
    )

    # Create two system messages
    messages: List[LLMMessage] = [
        SystemMessage(content="I am system message 1"),
        SystemMessage(content="I am system message 2"),
        UserMessage(content="Hello", source="user"),
    ]

    # Process the messages
    # pylint: disable=protected-access
    # The method is protected, but we need to test it
    create_params = client._process_create_args(  # pyright: ignore[reportPrivateUsage]
        messages=messages,
        tools=[],
        json_output=None,
        extra_create_args={},
        tool_choice="none",
    )

    # Extract the actual messages from the result
    oai_messages = create_params.messages

    # Check that there is only one system message and it contains the merged content
    system_messages = [msg for msg in oai_messages if msg["role"] == "system"]
    assert len(system_messages) == 1
    assert system_messages[0]["content"] == "I am system message 1\nI am system message 2"

    # Check that the user message is preserved
    user_messages = [msg for msg in oai_messages if msg["role"] == "user"]
    assert len(user_messages) == 1
    assert user_messages[0]["content"] == "Hello"