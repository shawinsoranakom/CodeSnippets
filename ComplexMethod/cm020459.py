async def test_reconfigure(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test successful reconfigure flow."""
    await setup_integration(hass, mock_config_entry)

    old_host = mock_config_entry.data[CONF_HOST]
    old_options = mock_config_entry.options

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: mock_config_entry.data[CONF_HOST]}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_receiver"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={OPTION_VOLUME_RESOLUTION: 200}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert mock_config_entry.data[CONF_HOST] == old_host
    assert mock_config_entry.options[OPTION_VOLUME_RESOLUTION] == 200
    for option, option_value in old_options.items():
        if option == OPTION_VOLUME_RESOLUTION:
            continue
        assert mock_config_entry.options[option] == option_value