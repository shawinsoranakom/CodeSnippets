async def test_user_flow_filters_already_configured_devices(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
) -> None:
    """Test already configured devices are filtered from discovery list."""
    # Add an existing configured entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AABBCCDDEEFF",
        data={CONF_HOST: "192.168.1.50"},
    )
    entry.add_to_hass(hass)

    # Mock zeroconf discovery with two devices
    mock_service_info_1 = AsyncServiceInfo(
        type_="_http._tcp.local.",
        name="shellyplus2pm-AABBCCDDEEFF._http._tcp.local.",
        port=80,
        addresses=[ip_address("192.168.1.100").packed],
        server="shellyplus2pm-AABBCCDDEEFF.local.",
    )
    mock_service_info_2 = AsyncServiceInfo(
        type_="_http._tcp.local.",
        name="shellyplus2pm-112233445566._http._tcp.local.",
        port=80,
        addresses=[ip_address("192.168.1.101").packed],
        server="shellyplus2pm-112233445566.local.",
    )
    mock_discovery.return_value = [mock_service_info_1, mock_service_info_2]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Check device list - should only have unconfigured device
    schema = result["data_schema"].schema
    device_selector = schema[CONF_DEVICE]
    options = {opt["value"]: opt["label"] for opt in device_selector.config["options"]}

    # Should NOT have the already configured device
    assert "AABBCCDDEEFF" not in options
    # Should have the new device
    assert "112233445566" in options
    # Should have manual entry
    assert "manual" in options

    # Select the unconfigured device and complete setup
    with (
        patch(
            "homeassistant.components.shelly.config_flow.get_info",
            return_value={
                "mac": "112233445566",
                "model": MODEL_PLUS_2PM,
                "auth": False,
                "gen": 2,
                "port": 80,
            },
        ),
        patch(
            "homeassistant.components.shelly.config_flow.RpcDevice.create",
            return_value=create_mock_rpc_device("Test Device"),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: "112233445566"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Device"
    assert result["data"][CONF_HOST] == "192.168.1.101"