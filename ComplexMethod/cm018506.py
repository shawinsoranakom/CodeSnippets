async def test_rpc_device_sensor_goes_unavailable_on_disconnect(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test RPC device with sensor goes unavailable on disconnect."""
    await init_integration(hass, 2)

    assert (state := hass.states.get("sensor.test_name_temperature"))
    assert state.state != STATE_UNAVAILABLE

    monkeypatch.setattr(mock_rpc_device, "connected", False)
    monkeypatch.setattr(mock_rpc_device, "initialized", False)
    mock_rpc_device.mock_disconnected()
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.test_name_temperature"))
    assert state.state == STATE_UNAVAILABLE

    freezer.tick(60)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert "NotInitialized" not in caplog.text

    monkeypatch.setattr(mock_rpc_device, "connected", True)
    monkeypatch.setattr(mock_rpc_device, "initialized", True)
    mock_rpc_device.mock_initialized()
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.test_name_temperature"))
    assert state.state != STATE_UNAVAILABLE