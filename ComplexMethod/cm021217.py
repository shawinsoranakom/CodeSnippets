async def test_reauth_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the reauth flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["handler"] == DOMAIN

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: NEW_TESTUSER,
            CONF_PASSWORD: NEW_TESTPASS,
        },
    )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"

    # Confirm that the config entry has been updated
    assert mock_config_entry.data[CONF_HOST] == HOMEE_IP
    assert mock_config_entry.data[CONF_USERNAME] == NEW_TESTUSER
    assert mock_config_entry.data[CONF_PASSWORD] == NEW_TESTPASS