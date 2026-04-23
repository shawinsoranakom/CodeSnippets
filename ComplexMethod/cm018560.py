async def test_user_flow_both_ble_and_zeroconf_prefers_zeroconf(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_rpc_device: Mock,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
) -> None:
    """Test device discovered via both BLE and Zeroconf prefers Zeroconf."""
    # Mock zeroconf discovery - same MAC as BLE device
    mock_discovery.return_value = [MOCK_SHELLY_ZEROCONF_SERVICE_INFO]

    # Inject BLE device with same MAC (from manufacturer data)
    # The manufacturer data contains WiFi MAC CCBA97C2D670
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO_GEN3)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Check device list - should only have one device (Zeroconf, not BLE)
    schema = result["data_schema"].schema
    device_selector = schema[CONF_DEVICE]
    options = {opt["value"]: opt["label"] for opt in device_selector.config["options"]}

    # Should have the device with MAC as key
    assert "CCBA97C2D670" in options
    assert options["CCBA97C2D670"] == "shellyplus2pm-CCBA97C2D670"
    # Should also have manual entry
    assert "manual" in options

    # Verify only 2 options (device + manual), not 3 (no duplicate)
    assert len(options) == 2

    # Select the device and verify it uses Zeroconf connection info
    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={
            "mac": "CCBA97C2D670",
            "model": MODEL_PLUS_2PM,
            "auth": False,
            "gen": 2,
            "port": 80,
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: "CCBA97C2D670"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Verify it used Zeroconf host (192.168.1.100) not BLE provisioning
    assert result["data"][CONF_HOST] == "192.168.1.100"
    assert result["data"][CONF_PORT] == 80