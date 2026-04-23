async def test_reauth_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_airobot_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauthentication flow."""
    mock_config_entry.add_to_hass(hass)

    # Trigger reauthentication
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"]["username"] == "T01A1B2C3"
    assert result["description_placeholders"]["host"] == "192.168.1.100"

    # Provide new password
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == "new-password"