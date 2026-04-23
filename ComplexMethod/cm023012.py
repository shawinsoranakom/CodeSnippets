async def test_chat_log_subscription(
    hass: HomeAssistant,
    mock_conversation_input: ConversationInput,
) -> None:
    """Test comprehensive chat log subscription functionality."""

    # Track all events received
    received_events = []

    def event_callback(
        conversation_id: str, event_type: ChatLogEventType, data: dict[str, Any]
    ) -> None:
        """Track received events."""
        received_events.append((conversation_id, event_type, data))

    # Subscribe to chat log events
    unsubscribe = async_subscribe_chat_logs(hass, event_callback)

    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        conversation_id = session.conversation_id

        # Test adding different types of content and verify events are sent
        chat_log.async_add_user_content(
            UserContent(
                content="Check this image",
                attachments=[
                    Attachment(
                        mime_type="image/jpeg",
                        media_content_id="media-source://bla",
                        path=Path("test_image.jpg"),
                    )
                ],
            )
        )
        # Check user content with attachments event
        assert received_events[-1][1] == ChatLogEventType.CONTENT_ADDED
        user_event = received_events[-1][2]["content"]
        assert user_event["content"] == "Check this image"
        assert len(user_event["attachments"]) == 1
        assert user_event["attachments"][0]["mime_type"] == "image/jpeg"

        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="test-agent", content="Hello! How can I help you?"
            )
        )
        # Check basic assistant content event
        assert received_events[-1][1] == ChatLogEventType.CONTENT_ADDED
        basic_event = received_events[-1][2]["content"]
        assert basic_event["content"] == "Hello! How can I help you?"
        assert basic_event["agent_id"] == "test-agent"

        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="test-agent",
                content="Let me think about that...",
                thinking_content="I need to analyze the user's request carefully.",
            )
        )
        # Check assistant content with thinking event
        assert received_events[-1][1] == ChatLogEventType.CONTENT_ADDED
        thinking_event = received_events[-1][2]["content"]
        assert (
            thinking_event["thinking_content"]
            == "I need to analyze the user's request carefully."
        )

        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="test-agent",
                content="Here's some data:",
                native={"type": "chart", "data": [1, 2, 3, 4, 5]},
            )
        )
        # Check assistant content with native event
        assert received_events[-1][1] == ChatLogEventType.CONTENT_ADDED
        native_event = received_events[-1][2]["content"]
        assert native_event["content"] == "Here's some data:"
        assert native_event["agent_id"] == "test-agent"

        chat_log.async_add_assistant_content_without_tools(
            ToolResultContent(
                agent_id="test-agent",
                tool_call_id="test-tool-call-123",
                tool_name="test_tool",
                tool_result="Tool execution completed successfully",
            )
        )
        # Check tool result content event
        assert received_events[-1][1] == ChatLogEventType.CONTENT_ADDED
        tool_result_event = received_events[-1][2]["content"]
        assert tool_result_event["tool_name"] == "test_tool"
        assert (
            tool_result_event["tool_result"] == "Tool execution completed successfully"
        )

        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="test-agent",
                content="I'll call an external service",
                tool_calls=[
                    llm.ToolInput(
                        id="external-tool-call-123",
                        tool_name="external_api_call",
                        tool_args={"endpoint": "https://api.example.com/data"},
                        external=True,
                    )
                ],
            )
        )
        # Check external tool call event
        assert received_events[-1][1] == ChatLogEventType.CONTENT_ADDED
        external_tool_event = received_events[-1][2]["content"]
        assert len(external_tool_event["tool_calls"]) == 1
        assert external_tool_event["tool_calls"][0].tool_name == "external_api_call"

    # Verify we received the expected events
    # Should have: 1 CREATED event + 7 CONTENT_ADDED events
    assert len(received_events) == 8

    # Check the first event is CREATED
    assert received_events[0][1] == ChatLogEventType.CREATED
    assert received_events[0][2]["chat_log"]["conversation_id"] == conversation_id

    # Check the second event is CONTENT_ADDED (from mock_conversation_input)
    assert received_events[1][1] == ChatLogEventType.CONTENT_ADDED
    assert received_events[1][0] == conversation_id

    # Test cleanup functionality
    assert conversation_id in hass.data[chat_session.DATA_CHAT_SESSION]

    # Set the last updated to be older than the timeout
    hass.data[chat_session.DATA_CHAT_SESSION][conversation_id].last_updated = (
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT
    )

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT * 2 + timedelta(seconds=1),
    )

    # Check that DELETED event was sent
    assert received_events[-1][1] == ChatLogEventType.DELETED
    assert received_events[-1][0] == conversation_id

    # Test that unsubscribing stops receiving events
    events_before_unsubscribe = len(received_events)
    unsubscribe()

    # Create a new session and add content - should not receive events
    with (
        chat_session.async_get_chat_session(hass) as session2,
        async_get_chat_log(hass, session2, mock_conversation_input) as chat_log2,
    ):
        chat_log2.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="test-agent", content="This should not be received"
            )
        )

    # Verify no new events were received after unsubscribing
    assert len(received_events) == events_before_unsubscribe