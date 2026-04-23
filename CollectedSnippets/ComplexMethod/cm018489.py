async def test_block_sleeping_binary_sensor(
    hass: HomeAssistant,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
) -> None:
    """Test block sleeping binary sensor."""
    entity_id = f"{BINARY_SENSOR_DOMAIN}.test_name_motion"
    await init_integration(hass, 1, sleep_period=1000)

    # Sensor should be created when device is online
    assert hass.states.get(entity_id) is None

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "motion", 1)
    mock_block_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-sensor_0-motion"