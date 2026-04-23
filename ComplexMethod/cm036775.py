async def test_streaming_message_synchronization(mock_parser):
    """Test message synchronization logic from lines 413-417 in context.py.

    This test verifies that when parser.messages contains more messages than
    the context's _messages (minus initial messages), the context properly
    extends its message list with the new parser messages.
    """

    # Create a streaming context with some initial messages
    initial_messages = [
        Message(
            author=Author(role=Role.USER, name="user"),
            content=[TextContent(text="Hello")],
            recipient=Role.ASSISTANT,
        )
    ]
    context = StreamingHarmonyContext(messages=initial_messages, available_tools=[])

    # Verify initial state
    assert len(context._messages) == 1
    assert context.num_init_messages == 1

    # Mock parser to have more messages than context
    # Simulate parser having processed 3 new messages
    mock_parser.messages = [
        Message(
            author=Author(role=Role.ASSISTANT, name="assistant"),
            content=[TextContent(text="Response 1")],
            recipient=Role.USER,
        ),
    ]

    # This should trigger the message synchronization logic
    context.append_output(
        create_mock_request_output(
            prompt_token_ids=[1, 2, 3], output_token_ids=[101], finished=False
        )
    )

    # Verify that messages were synchronized
    assert len(context._messages) == 2

    # Verify the new messages were added correctly
    assert context._messages[1].content[0].text == "Response 1"

    # Test the specific condition from line 413-414:
    # len(self._messages) - self.num_init_messages < len(self.parser.messages)
    messages_minus_init = len(context._messages) - context.num_init_messages
    parser_messages_count = len(mock_parser.messages)

    # After synchronization, they should be equal (no longer less than)
    assert messages_minus_init == parser_messages_count

    # Test edge case: add one more parser message
    mock_parser.messages.append(
        Message(
            author=Author(role=Role.ASSISTANT, name="assistant"),
            content=[TextContent(text="Response 4")],
            recipient=Role.USER,
        )
    )

    # Create another output to trigger synchronization again
    mock_output2 = create_mock_request_output(
        prompt_token_ids=[1, 2, 3], output_token_ids=[102], finished=True
    )

    context.append_output(mock_output2)

    # Verify the fourth message was added, num_init_messages is still 1
    assert len(context._messages) == 3
    assert context.num_init_messages == 1
    assert context._messages[2].content[0].text == "Response 4"