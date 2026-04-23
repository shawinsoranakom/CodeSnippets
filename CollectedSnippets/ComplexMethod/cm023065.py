async def test_reconfigure_flow_exceptions(
    hass: HomeAssistant,
    mock_powerfox_local_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test exceptions during reconfiguration flow."""
    mock_powerfox_local_client.value.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": error}

    # Recover from error
    mock_powerfox_local_client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"

    assert mock_config_entry.data[CONF_HOST] == "192.168.1.200"