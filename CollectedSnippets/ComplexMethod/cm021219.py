async def test_reconfigure_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homee: AsyncMock,
) -> None:
    """Test the reconfigure flow."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_homee
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["handler"] == DOMAIN

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: NEW_HOMEE_IP,
        },
    )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"

    # Confirm that the config entry has been updated
    assert mock_config_entry.data[CONF_HOST] == NEW_HOMEE_IP
    assert mock_config_entry.data[CONF_USERNAME] == TESTUSER
    assert mock_config_entry.data[CONF_PASSWORD] == TESTPASS