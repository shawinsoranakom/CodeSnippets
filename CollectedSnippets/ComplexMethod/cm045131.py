async def test_no_system_messages_for_gemini_model() -> None:
    """Tests behavior when no system messages are provided to a Gemini model."""
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
        },
    )

    # Create messages with no system message
    messages: List[LLMMessage] = [
        UserMessage(content="Hello", source="user"),
        AssistantMessage(content="Hi there", source="assistant"),
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

    # Check that there are no system messages
    system_messages = [msg for msg in oai_messages if msg["role"] == "system"]
    assert len(system_messages) == 0

    # Check that other messages are preserved
    user_messages = [msg for msg in oai_messages if msg["role"] == "user"]
    assistant_messages = [msg for msg in oai_messages if msg["role"] == "assistant"]
    assert len(user_messages) == 1
    assert len(assistant_messages) == 1