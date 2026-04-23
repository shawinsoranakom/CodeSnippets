async def test_user_flow_select_ble_device(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test selecting a BLE device goes to provisioning flow."""
    # Configure mock BLE device for this test
    mock_ble_rpc_device.wifi_scan.return_value = [
        {"ssid": "MyNetwork", "rssi": -50, "auth": 2}
    ]

    # Mock empty zeroconf discovery
    mock_discovery.return_value = []

    # Inject BLE device with RPC-over-BLE enabled (no discovery flow created)
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO_GEN3)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Select the BLE device
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DEVICE: "CCBA97C2D670"},  # MAC from manufacturer data
    )

    # Should go to bluetooth_confirm step
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

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
            return_value=("192.168.1.200", 80),
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
            {CONF_SSID: "MyNetwork", CONF_PASSWORD: "wifi_password"},
        )

        # Should show progress
        assert result["type"] is FlowResultType.SHOW_PROGRESS

        # Wait for provision task to complete
        await hass.async_block_till_done()

        # Complete provisioning
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should create entry
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "CCBA97C2D670"
    assert result["title"] == "Test name"