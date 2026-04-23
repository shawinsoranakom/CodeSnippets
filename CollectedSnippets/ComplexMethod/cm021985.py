async def test_connection_restore(
    mock_model_list: AsyncMock,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    mock_create_stream: AsyncMock,
) -> None:
    """Test background availability check restore on non-connectivity error."""
    mock_create_stream.side_effect = APITimeoutError(
        request=Request(method="POST", url=URL()),
    )

    # Check initial state
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unknown"

    # Get timeout
    await conversation.async_converse(
        hass, "hello", None, Context(), agent_id="conversation.claude_conversation"
    )

    # Check new state
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    mock_model_list.side_effect = APITimeoutError(
        request=Request(method="POST", url=URL()),
    )

    # Wait for background check to run and fail
    assert mock_model_list.await_count == 0
    test_time = datetime.datetime.now(datetime.UTC) + UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 1

    # Check state is still unavailable
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    # Now make the background check succeed
    mock_model_list.side_effect = None
    test_time += UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 2

    # Check that state is back to normal since the error is not connectivity related
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state != "unavailable"

    # Verify the background check period
    test_time += UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 2

    test_time += UPDATE_INTERVAL_CONNECTED - UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 3