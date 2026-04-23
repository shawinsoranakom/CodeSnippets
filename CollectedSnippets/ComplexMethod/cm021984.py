async def test_connection_check_reauth(
    mock_model_list: AsyncMock,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
) -> None:
    """Test authentication error during background availability check."""
    mock_model_list.side_effect = APITimeoutError(
        request=Request(method="POST", url=URL()),
    )

    # Check initial state
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unknown"

    # Get timeout
    assert mock_model_list.await_count == 0
    test_time = datetime.datetime.now(datetime.UTC) + UPDATE_INTERVAL_CONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 1

    # Check new state
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    mock_model_list.side_effect = AuthenticationError(
        message="Invalid API key",
        response=Response(status_code=403, request=Request(method="POST", url=URL())),
        body=None,
    )

    # Wait for background check to run and fail
    test_time += UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 2

    # Check state is still unavailable
    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    # Verify that the background check is not running anymore
    test_time += UPDATE_INTERVAL_DISCONNECTED
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()
    assert mock_model_list.await_count == 2

    # Check that a reauth flow has been created
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == mock_config_entry.entry_id