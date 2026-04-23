async def test_reconfigure(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the reconfigure flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "2.2.2.2",
            CONF_PASSWORD: "new-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "2.2.2.2"
    assert mock_config_entry.data[CONF_PASSWORD] == "new-password"
    assert mock_config_entry.data[CONF_SSL] is True
    assert mock_config_entry.data[CONF_VERIFY_SSL] is True
    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1