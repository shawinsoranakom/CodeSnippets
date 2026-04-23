async def test_connection_error_handling(
    mock_model_list: AsyncMock,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    mock_create_stream: AsyncMock,
) -> None:
    """Test making entity unavailable on connection error."""
    mock_create_stream.side_effect = APITimeoutError(
        request=Request(method="POST", url=URL()),
    )

    # Check initial state
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unknown"

    # Get timeout
    result = await conversation.async_converse(
        hass, "hello", None, Context(), agent_id="conversation.claude_conversation"
    )

    assert result.response.response_type == intent.IntentResponseType.ERROR
    assert result.response.error_code == "unknown", result

    # Check new state
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    # Try again
    await conversation.async_converse(
        hass, "hello", None, Context(), agent_id="conversation.claude_conversation"
    )

    # Check state is still unavailable
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    mock_create_stream.side_effect = RateLimitError(
        message=None,
        response=Response(status_code=429, request=Request(method="POST", url=URL())),
        body=None,
    )

    # Get a different error meaning the connection is restored
    await conversation.async_converse(
        hass, "hello", None, Context(), agent_id="conversation.claude_conversation"
    )

    # Check state is back to normal
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "2026-02-27T12:00:00+00:00"

    # Verify the background check period
    test_time = datetime.datetime.now(datetime.UTC) + UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    mock_model_list.assert_not_awaited()

    test_time += UPDATE_INTERVAL_CONNECTED - UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    mock_model_list.assert_awaited_once()