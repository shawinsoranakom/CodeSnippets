async def test_block_rest_binary_sensor_connected_battery_devices(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test block REST binary sensor for connected battery devices."""
    entity_id = register_entity(hass, BINARY_SENSOR_DOMAIN, "test_name_cloud", "cloud")
    monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
    monkeypatch.setitem(mock_block_device.settings["device"], "type", MODEL_MOTION)
    monkeypatch.setitem(mock_block_device.settings["coiot"], "update_period", 3600)
    await init_integration(hass, 1, model=MODEL_MOTION)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    monkeypatch.setitem(mock_block_device.status["cloud"], "connected", True)

    # Verify no update on fast intervals
    await mock_rest_update(hass, freezer)
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    # Verify update on slow intervals
    await mock_rest_update(hass, freezer, seconds=UPDATE_PERIOD_MULTIPLIER * 3600)
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-cloud"