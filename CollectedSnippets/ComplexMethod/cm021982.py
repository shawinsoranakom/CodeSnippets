async def test_auth_error_handling(
    mock_model_list: AsyncMock,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    mock_create_stream: AsyncMock,
) -> None:
    """Test reauth after authentication error during conversation."""
    # This is an assumption of the tests, not the main code:
    assert UPDATE_INTERVAL_DISCONNECTED < UPDATE_INTERVAL_CONNECTED

    mock_create_stream.side_effect = mock_model_list.side_effect = AuthenticationError(
        message="Invalid API key",
        response=Response(status_code=403, request=Request(method="POST", url=URL())),
        body=None,
    )

    result = await conversation.async_converse(
        hass, "hello", None, Context(), agent_id="conversation.claude_conversation"
    )

    assert result.response.response_type == intent.IntentResponseType.ERROR
    assert result.response.error_code == "unknown", result

    await hass.async_block_till_done()

    state = hass.states.get("conversation.claude_conversation")
    assert state
    assert state.state == "unavailable"

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert "context" in flow
    assert flow["context"]["source"] == SOURCE_REAUTH
    assert flow["context"]["entry_id"] == mock_config_entry.entry_id