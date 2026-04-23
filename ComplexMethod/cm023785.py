async def test_dhcp_discovery(
    hass: HomeAssistant, mock_teltasync_client: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    """Test DHCP discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            macaddress="209727112233",
            hostname="teltonika",
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"
    assert "name" in result["description_placeholders"]
    assert "host" in result["description_placeholders"]

    # Configure device info for the actual setup
    device_info = MagicMock()
    device_info.device_name = "RUTX50 Discovered"
    device_info.device_identifier = "DISCOVERED123"
    mock_teltasync_client.get_device_info.return_value = device_info

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RUTX50 Discovered"
    assert result["data"][CONF_HOST] == "https://192.168.1.50"
    assert result["data"][CONF_USERNAME] == "admin"
    assert result["data"][CONF_PASSWORD] == "password"
    assert result["result"].unique_id == "DISCOVERED123"