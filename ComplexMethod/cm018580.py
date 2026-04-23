async def test_bluetooth_wifi_scan_failure(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test WiFi scan failure via BLE."""
    # Configure mock BLE device to fail first, then succeed
    mock_ble_rpc_device.wifi_scan.side_effect = DeviceConnectionError

    # Inject BLE device so it's available in the bluetooth scanner
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=BLE_DISCOVERY_INFO,
        context={"source": config_entries.SOURCE_BLUETOOTH},
    )

    # Confirm - wifi scan will fail
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "wifi_scan_failed"

    # Now configure success for retry
    mock_ble_rpc_device.wifi_scan.side_effect = None
    mock_ble_rpc_device.wifi_scan.return_value = [
        {"ssid": "Network1", "rssi": -50, "auth": 2}
    ]

    # Test retry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "wifi_scan"

    # Select network and enter password to complete provisioning
    with (
        patch(
            "homeassistant.components.shelly.config_flow.async_lookup_device_by_name",
            return_value=("1.1.1.1", 80),
        ),
        patch(
            "homeassistant.components.shelly.config_flow.get_info",
            return_value=MOCK_DEVICE_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SSID: "Network1", CONF_PASSWORD: "my_password"},
        )

        # Provisioning shows progress
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        await hass.async_block_till_done()

        # Complete provisioning
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "C049EF8873E8"
    assert result["title"] == "Test name"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: 80,
        CONF_MODEL: MODEL_PLUS_2PM,
        CONF_SLEEP_PERIOD: 0,
        CONF_GEN: 2,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1