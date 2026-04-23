async def test_rpc_sleeping_binary_sensor(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test RPC online sleeping binary sensor."""
    entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_cloud"
    monkeypatch.setattr(mock_rpc_device, "connected", False)
    monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
    config_entry = await init_integration(hass, 2, sleep_period=1000)

    # Sensor should be created when device is online
    assert hass.states.get(entity_id) is None

    register_entity(
        hass, BINARY_SENSOR_DOMAIN, "test_name_cloud", "cloud-cloud", config_entry
    )

    # Make device online
    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cloud", "connected", True)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    # test external power sensor
    assert (state := hass.states.get("binary_sensor.test_name_external_power"))
    assert state.state == STATE_ON

    assert (
        entry := entity_registry.async_get("binary_sensor.test_name_external_power")
    )
    assert entry.unique_id == "123456789ABC-devicepower:0-external_power"