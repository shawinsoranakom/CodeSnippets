async def test_dhcp_discovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_airobot_client: AsyncMock,
) -> None:
    """Test DHCP discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            macaddress="b8d61aabcdef",
            hostname="airobot-thermostat-t01a1b2c3",
        ),
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"
    assert result["description_placeholders"] == {
        "host": "192.168.1.100",
        "device_id": "T01A1B2C3",
    }

    # Complete the flow by providing password only
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "test-password"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Thermostat"
    assert result["data"][CONF_HOST] == "192.168.1.100"
    assert result["data"][CONF_USERNAME] == "T01A1B2C3"
    assert result["data"][CONF_PASSWORD] == "test-password"
    assert result["data"][CONF_MAC] == "b8d61aabcdef"