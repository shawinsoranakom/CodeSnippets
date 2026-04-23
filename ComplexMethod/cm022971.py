async def test_full_reconfigure_flow_connection_error_and_success(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_wled: MagicMock
) -> None:
    """Test we show user form on WLED connection error and allows user to change host."""
    mock_config_entry.add_to_hass(hass)

    # Mock connection error
    mock_wled.update.side_effect = WLEDConnectionError

    result = await mock_config_entry.start_reconfigure_flow(hass)

    # Assert show form initially
    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM

    # Input new host value
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    # Assert form with errors
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {"base": "cannot_connect"}

    # Remove mock for connection error
    mock_wled.update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    # Assert show text message and close flow
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"

    # Assert config entry has been updated.
    assert mock_config_entry.data[CONF_HOST] == "10.10.0.10"