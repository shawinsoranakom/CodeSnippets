async def test_user_flow_includes_ignored_devices(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
) -> None:
    """Test ignored devices are included in discovery list for reconfiguration."""
    # Add an ignored entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AABBCCDDEEFF",
        data={CONF_HOST: "192.168.1.50"},
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)

    # Mock zeroconf discovery with the ignored device
    mock_discovery.return_value = [MOCK_HTTP_ZEROCONF_SERVICE_INFO]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Check device list - should include the ignored device
    schema = result["data_schema"].schema
    device_selector = schema[CONF_DEVICE]
    options = {opt["value"]: opt["label"] for opt in device_selector.config["options"]}

    # Should have the ignored device (for potential reconfiguration)
    assert "AABBCCDDEEFF" in options
    assert options["AABBCCDDEEFF"] == "shellyplus2pm-AABBCCDDEEFF"

    # Select the ignored device and complete setup
    with (
        patch(
            "homeassistant.components.shelly.config_flow.get_info",
            return_value={
                "mac": "AABBCCDDEEFF",
                "model": MODEL_PLUS_2PM,
                "auth": False,
                "gen": 2,
                "port": 80,
            },
        ),
        patch(
            "homeassistant.components.shelly.config_flow.RpcDevice.create",
            return_value=create_mock_rpc_device("Test Ignored Device"),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: "AABBCCDDEEFF"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Ignored Device"