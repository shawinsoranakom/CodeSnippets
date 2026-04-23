async def test_block_sleeping_sensor(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block sleeping sensor."""
    monkeypatch.setattr(
        mock_block_device.blocks[DEVICE_BLOCK_ID], "sensor_ids", {"battery": 98}
    )
    entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
    await init_integration(hass, 1, sleep_period=1000)

    # Sensor should be created when device is online
    assert hass.states.get(entity_id) is None

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == "22.1"

    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "temp", 23.4)
    mock_block_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == "23.4"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-sensor_0-temp"