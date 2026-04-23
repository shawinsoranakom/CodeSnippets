async def test_dhcp_confirm_error_with_recovery(
    hass: HomeAssistant,
    mock_teltasync_client: MagicMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    error_key: str,
) -> None:
    """Test DHCP confirmation handles errors and can recover."""
    # Start the DHCP flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            macaddress="209727112233",
            hostname="teltonika",
        ),
    )

    # First attempt with error
    mock_teltasync_client.get_device_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_key}
    assert result["step_id"] == "dhcp_confirm"

    # Recover with working connection
    device_info = MagicMock()
    device_info.device_name = "RUTX50 Discovered"
    device_info.device_identifier = "DISCOVERED123"
    mock_teltasync_client.get_device_info.side_effect = None
    mock_teltasync_client.get_device_info.return_value = device_info
    mock_teltasync_client.validate_credentials.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RUTX50 Discovered"
    assert result["data"][CONF_HOST] == "https://192.168.1.50"
    assert result["result"].unique_id == "DISCOVERED123"