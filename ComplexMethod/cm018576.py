async def test_bluetooth_discovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test bluetooth discovery and complete provisioning."""
    # Configure mock BLE device for this test
    mock_ble_rpc_device.wifi_scan.return_value = [
        {"ssid": "MyNetwork", "rssi": -50, "auth": 2}
    ]

    # Inject BLE device so it's available in the bluetooth scanner
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=BLE_DISCOVERY_INFO,
        context={"source": config_entries.SOURCE_BLUETOOTH},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["description_placeholders"]["name"] == "ShellyPlus2PM-C049EF8873E8"

    # Confirm - BLE device will be used for wifi_scan via fixture
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

        # Provisioning happens in background, shows progress
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        await hass.async_block_till_done()

        # Complete provisioning by configuring the progress step
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Provisioning should complete and create entry
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