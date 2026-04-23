async def test_full_flow_reconfigure_exceptions(
    hass: HomeAssistant,
    mock_proxmox_client: MagicMock,
    mock_setup_entry: MagicMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    reason: str,
) -> None:
    """Test the full flow of the config flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_proxmox_client.nodes.get.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_STEP,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_AUTH_STEP_PASSWORD,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": reason}

    mock_proxmox_client.nodes.get.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_AUTH_STEP_PASSWORD,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    sanitized = sanitize_config_entry(mock_config_entry.data)
    assert sanitized == MOCK_TEST_CONFIG