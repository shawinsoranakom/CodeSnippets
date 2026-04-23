async def test_entry_unload_not_connected_but_we_think_we_are(
    hass: HomeAssistant, mock_rpc_device: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test entry unload when not connected but we think we are still connected."""
    monkeypatch.delitem(mock_rpc_device.status, "cover:0")
    monkeypatch.setitem(mock_rpc_device.status["sys"], "relay_in_thermostat", False)

    with patch(
        "homeassistant.components.shelly.coordinator.async_stop_scanner",
        side_effect=DeviceConnectionError,
    ) as mock_stop_scanner:
        assert (
            entry := await init_integration(
                hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
            )
        )
        assert entry.state is ConfigEntryState.LOADED

        assert (state := hass.states.get("switch.test_name_test_switch_0"))
        assert state.state == STATE_ON
        assert not mock_stop_scanner.call_count

        monkeypatch.setattr(mock_rpc_device, "connected", False)

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    assert not mock_stop_scanner.call_count
    assert entry.state is ConfigEntryState.LOADED