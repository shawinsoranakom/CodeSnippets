async def test_dhcp_flow(hass: HomeAssistant, mock_setup_entry: MagicMock) -> None:
    """Successful flow from DHCP discovery."""
    dhcp_data = DhcpServiceInfo(
        ip=TEST_HOST,
        hostname="Reolink",
        macaddress=DHCP_FORMATTED_MAC,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=dhcp_data
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NVR_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: TEST_PORT,
        CONF_USE_HTTPS: TEST_USE_HTTPS,
        CONF_SUPPORTS_PRIVACY_MODE: TEST_PRIVACY,
        CONF_BC_PORT: TEST_BC_PORT,
        CONF_BC_ONLY: False,
    }
    assert result["options"] == {
        CONF_PROTOCOL: DEFAULT_PROTOCOL,
    }