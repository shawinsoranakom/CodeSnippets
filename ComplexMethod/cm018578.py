async def test_bluetooth_factory_reset_rediscovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test device can be rediscovered after factory reset when RPC-over-BLE is re-enabled."""
    # Configure mock BLE device for this test
    mock_ble_rpc_device.wifi_scan.return_value = [
        {"ssid": "MyNetwork", "rssi": -50, "auth": 2}
    ]

    # First discovery: device is already provisioned (no RPC-over-BLE)
    # Inject the device without RPC so it's in the bluetooth scanner
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO_NO_RPC)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=BLE_DISCOVERY_INFO_NO_RPC,
        context={"source": config_entries.SOURCE_BLUETOOTH},
    )

    # Should abort because RPC-over-BLE is not enabled
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_discovery_info"

    # Simulate factory reset: device now advertises with RPC-over-BLE enabled
    # Inject the updated advertisement
    inject_bluetooth_service_info_bleak(hass, BLE_DISCOVERY_INFO)

    # Second discovery: device after factory reset (RPC-over-BLE now enabled)
    # Wait for automatic discovery to happen
    await hass.async_block_till_done()

    # Find the flow that was automatically created
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]

    # Should successfully start config flow since match history was cleared
    assert result["step_id"] == "bluetooth_confirm"
    assert (
        result["context"]["title_placeholders"]["name"] == "ShellyPlus2PM-C049EF8873E8"
    )

    # Confirm - wifi_scan handled by fixture
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    # Select network and enter password to provision
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
            {CONF_SSID: "MyNetwork", CONF_PASSWORD: "my_password"},
        )

        # Provisioning happens in background
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        await hass.async_block_till_done()

        # Complete provisioning
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Provisioning should complete and create entry
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "C049EF8873E8"