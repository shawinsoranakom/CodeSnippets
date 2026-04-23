async def test_async_step_reauth_invalid_key(
    hass: HomeAssistant,
    mock_config_entry_added_to_hass: MockConfigEntry,
    mock_discovered_service_info: AsyncMock,
) -> None:
    """Test reauth flow with an invalid key shows error and allows retry."""
    result = await mock_config_entry_added_to_hass.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Submit wrong key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_TEST_WRONG_TOKEN},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_access_token"}

    # Now submit correct key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: VICTRON_VEBUS_TOKEN},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"