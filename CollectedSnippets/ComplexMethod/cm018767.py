async def test_reauth_recovery_after_error(
    hass: HomeAssistant,
    exception_type: Exception,
    expected_error: str,
    mock_config_entry: MockConfigEntry,
    mock_pterodactyl: Generator[AsyncMock],
) -> None:
    """Test recovery after an error during re-authentication."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_pterodactyl.client.servers.list_servers.side_effect = exception_type

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: TEST_API_KEY}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    mock_pterodactyl.reset_mock(side_effect=True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: TEST_API_KEY}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_URL] == TEST_URL
    assert mock_config_entry.data[CONF_API_KEY] == TEST_API_KEY