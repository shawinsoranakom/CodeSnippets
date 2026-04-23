async def test_dhcp_discovery_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_airobot_client: AsyncMock,
    exception: Exception,
    error_base: str,
) -> None:
    """Test DHCP discovery with error handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            macaddress="aabbccddeeff",
            hostname="airobot-thermostat-t01d4e5f6",
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"

    mock_airobot_client.get_statuses.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "wrong"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_base}

    # Recover from error
    mock_airobot_client.get_statuses.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "test-password"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Thermostat"
    assert len(mock_setup_entry.mock_calls) == 1