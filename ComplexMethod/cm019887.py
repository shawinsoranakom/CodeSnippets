async def test_reauth_flow_clears_credentials(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test reauthentication flow clears credentials when submitted empty."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
            CONF_SSL: False,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_USERNAME] is None
    assert mock_config_entry.data[CONF_PASSWORD] is None
    assert mock_config_entry.data[CONF_SSL] is False