async def test_reauth_flow_error_and_recover(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_victron_hub: MagicMock,
    exception: Exception,
    error: str,
) -> None:
    """Test reauthentication flow handles errors and allows recovery."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_victron_hub.return_value.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "wrong-user",
            CONF_PASSWORD: "wrong-password",
            CONF_SSL: False,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    # Recover from error
    mock_victron_hub.return_value.connect.side_effect = None
    mock_victron_hub.return_value.installation_id = MOCK_INSTALLATION_ID

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "new-user",
            CONF_PASSWORD: "new-password",
            CONF_SSL: True,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_USERNAME] == "new-user"
    assert mock_config_entry.data[CONF_PASSWORD] == "new-password"
    assert mock_config_entry.data[CONF_SSL] is True