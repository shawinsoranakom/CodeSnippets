async def test_bluetooth_wifi_credentials_and_provision_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test successful WiFi provisioning via BLE."""
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

    # Confirm BLE provisioning - wifi_scan handled by fixture
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "wifi_scan"

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

        # Should show progress
        assert result["type"] is FlowResultType.SHOW_PROGRESS

        # Wait for provision task to complete
        await hass.async_block_till_done()

        # Complete provisioning
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should create entry
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
    mock_ble_rpc_device.wifi_setconfig.assert_called_once()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1