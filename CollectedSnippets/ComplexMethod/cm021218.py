async def test_reauth_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homee: AsyncMock,
    side_eff: Exception,
    error: dict[str, str],
) -> None:
    """Test reconfigure flow errors."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_homee.get_access_token.side_effect = side_eff
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: NEW_TESTUSER,
            CONF_PASSWORD: NEW_TESTPASS,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == error

    # Confirm that the config entry is unchanged
    assert mock_config_entry.data[CONF_USERNAME] == TESTUSER
    assert mock_config_entry.data[CONF_PASSWORD] == TESTPASS

    mock_homee.get_access_token.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: NEW_TESTUSER,
            CONF_PASSWORD: NEW_TESTPASS,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    # Confirm that the config entry has been updated
    assert mock_config_entry.data[CONF_HOST] == HOMEE_IP
    assert mock_config_entry.data[CONF_USERNAME] == NEW_TESTUSER
    assert mock_config_entry.data[CONF_PASSWORD] == NEW_TESTPASS