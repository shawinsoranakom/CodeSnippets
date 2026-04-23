async def test_dhcp_discovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_ring_client: Mock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test discovery by dhcp."""
    mac_address = "1234567890abcd"
    hostname = "Ring-90abcd"
    ip_address = "127.0.0.1"
    username = "hello@home-assistant.io"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(ip=ip_address, macaddress=mac_address, hostname=hostname),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"
    with patch("uuid.uuid4", return_value=MOCK_HARDWARE_ID):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": username, "password": "test-password"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "hello@home-assistant.io"
    assert result["data"] == {
        CONF_DEVICE_ID: MOCK_HARDWARE_ID,
        CONF_USERNAME: username,
        CONF_TOKEN: {"access_token": "mock-token"},
    }

    config_entry = hass.config_entries.async_entry_for_domain_unique_id(
        DOMAIN, username
    )
    assert config_entry

    # Create a device entry under the config entry just created
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, mac_address)},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(ip=ip_address, macaddress=mac_address, hostname=hostname),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"