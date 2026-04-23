async def test_reconfigure_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homee: AsyncMock,
    side_eff: Exception,
    error: dict[str, str],
) -> None:
    """Test reconfigure flow errors."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_homee
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_homee.get_access_token.side_effect = side_eff
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: NEW_HOMEE_IP,
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == error

    # Confirm that the config entry is unchanged
    assert mock_config_entry.data[CONF_HOST] == HOMEE_IP

    mock_homee.get_access_token.side_effect = None
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