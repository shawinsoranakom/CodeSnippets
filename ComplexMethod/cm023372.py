async def test_reconfigure_errors(
    hass: HomeAssistant,
    mock_nsapi: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test reconfigure flow error handling (invalid auth and cannot connect)."""
    mock_config_entry.add_to_hass(hass)

    # First present the form
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Make get_stations raise the requested exception
    mock_nsapi.get_stations.side_effect = exception

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "bad_key"}
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": expected_error}

    # Clear side effect and submit valid API key to complete the flow
    mock_nsapi.get_stations.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "new_valid_key"}
    )

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_API_KEY] == "new_valid_key"