async def test_first_user_message_with_identical_content(
    test_event_stream, mock_agent_with_stats
):
    """Test that _first_user_message correctly identifies the first user message.

    This test verifies that messages with identical content but different IDs are properly
    distinguished, and that the result is correctly cached.

    The issue we're checking is that the comparison (action == self._first_user_message())
    should correctly differentiate between messages with the same content but different IDs.
    """
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    controller = AgentController(
        agent=mock_agent,
        event_stream=test_event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create and add the first user message
    first_message = MessageAction(content='Hello, this is a test message')
    first_message._source = EventSource.USER
    test_event_stream.add_event(first_message, EventSource.USER)

    # Create and add a second user message with identical content
    second_message = MessageAction(content='Hello, this is a test message')
    second_message._source = EventSource.USER
    test_event_stream.add_event(second_message, EventSource.USER)

    # Verify that _first_user_message returns the first message
    first_user_message = controller._first_user_message()
    assert first_user_message is not None
    assert first_user_message.id == first_message.id  # Check IDs match
    assert first_user_message.id != second_message.id  # Different IDs
    assert first_user_message == first_message == second_message  # dataclass equality

    # Test the comparison used in the actual code
    assert first_message == first_user_message  # This should be True
    assert (
        second_message.id != first_user_message.id
    )  # This should be False, but may be True if there's a bug

    # Verify caching behavior
    assert (
        controller._cached_first_user_message is not None
    )  # Cache should be populated
    assert (
        controller._cached_first_user_message is first_user_message
    )  # Cache should store the same object

    # Mock get_events to verify it's not called again
    with patch.object(test_event_stream, 'get_events') as mock_get_events:
        cached_message = controller._first_user_message()
        assert cached_message is first_user_message  # Should return cached object
        mock_get_events.assert_not_called()  # Should not call get_events again

    await controller.close()