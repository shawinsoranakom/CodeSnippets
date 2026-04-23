async def test_chat(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    agent_id: str,
) -> None:
    """Test that the chat function is called with the appropriate arguments."""

    if agent_id is None:
        agent_id = mock_config_entry.entry_id

    entry = MockConfigEntry()
    entry.add_to_hass(hass)

    with patch(
        "ollama.AsyncClient.chat",
        return_value=stream_generator(
            {"message": {"role": "assistant", "content": "test response"}}
        ),
    ) as mock_chat:
        result = await conversation.async_converse(
            hass,
            "test message",
            None,
            Context(),
            agent_id=agent_id,
        )

        assert mock_chat.call_count == 1
        args = mock_chat.call_args.kwargs
        prompt = args["messages"][0]["content"]

        assert args["model"] == "test_model:latest"
        assert args["messages"] == [
            Message(role="system", content=prompt),
            Message(role="user", content="test message"),
        ]

        assert result.response.response_type == intent.IntentResponseType.ACTION_DONE, (
            result
        )
        assert result.response.speech["plain"]["speech"] == "test response"

    # Test Conversation tracing
    traces = trace.async_get_traces()
    assert traces
    last_trace = traces[-1].as_dict()
    trace_events = last_trace.get("events", [])
    assert [event["event_type"] for event in trace_events] == [
        trace.ConversationTraceEventType.ASYNC_PROCESS,
        trace.ConversationTraceEventType.AGENT_DETAIL,
    ]
    # AGENT_DETAIL event contains the raw prompt passed to the model
    detail_event = trace_events[1]
    assert (
        "You are a voice assistant for Home Assistant."
        in detail_event["data"]["messages"][0]["content"]
    )