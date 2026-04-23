async def test_zeroconf_aborts_idle_ble_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_setup: AsyncMock,
) -> None:
    """Test zeroconf discovery aborts idle BLE flow (lines 316-321)."""
    # Start BLE discovery flow and leave it idle at bluetooth_confirm
    await _async_inject_ble_discovery(hass, BLE_DISCOVERY_INFO)

    ble_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=BLE_DISCOVERY_INFO,
        context={"source": config_entries.SOURCE_BLUETOOTH},
    )

    assert ble_result["type"] is FlowResultType.FORM
    assert ble_result["step_id"] == "bluetooth_confirm"
    ble_flow_id = ble_result["flow_id"]

    # Now start zeroconf discovery for the same device - should abort BLE flow
    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value=MOCK_DEVICE_INFO,
    ):
        zeroconf_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.1.1.1"),
                ip_addresses=[ip_address("1.1.1.1")],
                hostname="shelly2pm-c049ef8873e8.local.",
                name="shelly2pm-c049ef8873e8",
                port=80,
                properties={"gen": "2"},
                type="_http._tcp.local.",
            ),
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    # Verify BLE flow was aborted
    flows = hass.config_entries.flow.async_progress()
    assert not any(flow["flow_id"] == ble_flow_id for flow in flows)

    # Complete zeroconf flow
    assert zeroconf_result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        zeroconf_result["flow_id"], {}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "C049EF8873E8"
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1