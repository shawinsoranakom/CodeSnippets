async def test_reauth_flow_success(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test reauthentication flow with successful credentials."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}

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