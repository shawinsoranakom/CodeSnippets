async def test_tool_calls_assistant_message_content_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that AssistantMessage with tool calls includes required content field.

    This test addresses the issue where AssistantMessage with tool calls but no thought
    was missing the required 'content' field, causing OpenAI API UnprocessableEntityError(422).
    """
    # Create a tool call for testing
    tool_calls = [
        FunctionCall(id="call_1", name="increment_number", arguments='{"number": 5}'),
        FunctionCall(id="call_2", name="increment_number", arguments='{"number": 6}'),
    ]

    # Mock response for tool calls
    chat_completion = ChatCompletion(
        id="id1",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="Done",
                ),
            )
        ],
        created=1234567890,
        model="gpt-4o",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=10, prompt_tokens=5, total_tokens=15),
    )

    client = OpenAIChatCompletionClient(model="gpt-4o", api_key="test")
    mock_create = AsyncMock(return_value=chat_completion)

    # Test AssistantMessage with tool calls but no thought
    assistant_message_no_thought = AssistantMessage(
        content=tool_calls,
        source="assistant",
        thought=None,  # No thought - this was causing the issue
    )

    with monkeypatch.context() as mp:
        mp.setattr(client._client.chat.completions, "create", mock_create)  # type: ignore[reportPrivateUsage]

        await client.create(
            messages=[
                UserMessage(content="Please increment these numbers", source="user"),
                assistant_message_no_thought,
            ]
        )

    # Verify the API was called and check the messages sent
    mock_create.assert_called_once()
    call_args = mock_create.call_args

    # Extract the messages from the API call
    messages = call_args.kwargs["messages"]

    # Find the assistant message in the API call
    assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
    assert len(assistant_messages) == 1

    assistant_msg = assistant_messages[0]

    # Verify all required fields are present
    assert "role" in assistant_msg
    assert "tool_calls" in assistant_msg
    assert "content" in assistant_msg  # This was missing before the fix

    # Verify field values
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"] is None  # Should be null for tools without thought
    assert len(assistant_msg["tool_calls"]) == 2

    # Test AssistantMessage with tool calls AND thought
    assistant_message_with_thought = AssistantMessage(
        content=tool_calls, source="assistant", thought="I need to increment these numbers."
    )

    mock_create.reset_mock()  # Reset for second test

    with monkeypatch.context() as mp:
        mp.setattr(client._client.chat.completions, "create", mock_create)  # type: ignore[reportPrivateUsage]

        await client.create(
            messages=[
                UserMessage(content="Please increment these numbers", source="user"),
                assistant_message_with_thought,
            ]
        )

    # Verify the API was called for the second test
    mock_create.assert_called_once()
    call_args = mock_create.call_args

    # Extract the messages from the API call
    messages = call_args.kwargs["messages"]

    # Find the assistant message in the API call
    assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
    assert len(assistant_messages) == 1

    assistant_msg_with_thought = assistant_messages[0]

    # Should have both tool_calls and content with thought text
    assert "role" in assistant_msg_with_thought
    assert "tool_calls" in assistant_msg_with_thought
    assert "content" in assistant_msg_with_thought
    assert assistant_msg_with_thought["role"] == "assistant"
    assert assistant_msg_with_thought["content"] == "I need to increment these numbers."
    assert len(assistant_msg_with_thought["tool_calls"]) == 2