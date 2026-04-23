async def test_user_flow_with_ble_devices(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test user flow shows discovered BLE devices."""
    # Configure mock BLE device for this test
    mock_ble_rpc_device.wifi_scan.return_value = [
        {"ssid": "TestNetwork", "rssi": -50, "auth": 2}
    ]

    # Mock empty zeroconf discovery
    mock_discovery.return_value = []

    # Inject BLE device with RPC-over-BLE enabled
    # The manufacturer data contains WiFi MAC CCBA97C2D670
    await _async_inject_ble_discovery(
        hass,
        BluetoothServiceInfoBleak(
            name="ShellyPlusGen3",  # Name without MAC so it uses manufacturer data
            address="AA:BB:CC:DD:EE:FF",
            rssi=-60,
            manufacturer_data=BLE_MANUFACTURER_DATA_WITH_MAC,
            service_data={},
            service_uuids=[],
            source="local",
            device=generate_ble_device(
                address="AA:BB:CC:DD:EE:FF",
                name="ShellyPlusGen3",
            ),
            advertisement=generate_advertisement_data(
                manufacturer_data=BLE_MANUFACTURER_DATA_WITH_MAC,
            ),
            time=0,
            connectable=True,
            tx_power=-127,
        ),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Should show form with discovered BLE device
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Check device is in the options
    schema = result["data_schema"].schema
    device_selector = schema[CONF_DEVICE]
    options = {opt["value"]: opt["label"] for opt in device_selector.config["options"]}

    # Should have the discovered BLE device plus manual entry
    # MAC from manufacturer data: CCBA97C2D670
    assert "CCBA97C2D670" in options
    assert "manual" in options
    # Device name should be from model ID + MAC
    assert "Shelly1MiniGen4-CCBA97C2D670" in options["CCBA97C2D670"]

    # Select the BLE device and complete provisioning flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DEVICE: "CCBA97C2D670"},
    )

    # Should go to bluetooth_confirm step
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Confirm BLE provisioning - wifi_scan is handled by fixture
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    # Select network and enter WiFi credentials to complete
    with (
        patch(
            "homeassistant.components.shelly.config_flow.async_lookup_device_by_name",
            return_value=("192.168.1.100", 80),
        ),
        patch(
            "homeassistant.components.shelly.config_flow.get_info",
            return_value={
                "mac": "CCBA97C2D670",
                "model": MODEL_PLUS_2PM,
                "auth": False,
                "gen": 2,
            },
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SSID: "TestNetwork", CONF_PASSWORD: "test_password"},
        )

        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should create entry
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "CCBA97C2D670"