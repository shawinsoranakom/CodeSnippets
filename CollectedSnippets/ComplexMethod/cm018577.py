async def test_bluetooth_provisioning_clears_match_history(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
    mock_ble_rpc_device: AsyncMock,
) -> None:
    """Test bluetooth provisioning clears match history at discovery start and after successful provisioning."""
    # Configure mock BLE device for this test
    mock_ble_rpc_device.wifi_scan.return_value = [
        {"ssid": "MyNetwork", "rssi": -50, "auth": 2}
    ]

    # Inject BLE device so it's available in the bluetooth scanner
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO_FOR_CLEAR_TEST)

    with patch(
        "homeassistant.components.shelly.config_flow.async_clear_address_from_match_history",
    ) as mock_clear:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=BLE_DISCOVERY_INFO_FOR_CLEAR_TEST,
            context={"source": config_entries.SOURCE_BLUETOOTH},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "bluetooth_confirm"

        # Confirm - wifi_scan handled by fixture
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        # Reset mock to only count calls during provisioning
        mock_clear.reset_mock()

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
        assert result["result"].unique_id == "AABBCCDDEE00"

        # Verify match history was cleared once during provisioning
        # Only count calls with our test device's address to avoid interference from other tests
        our_device_calls = [
            call
            for call in mock_clear.call_args_list
            if len(call.args) > 1
            and call.args[1] == BLE_DISCOVERY_INFO_FOR_CLEAR_TEST.address
        ]
        assert our_device_calls
        mock_clear.assert_called_with(hass, BLE_DISCOVERY_INFO_FOR_CLEAR_TEST.address)