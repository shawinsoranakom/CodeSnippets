async def test_sensor_platform(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_get: AsyncMock,
    mock_update: AsyncMock,
) -> None:
    """Test sensor platform."""

    await add_mock_config(hass)

    # Test First TimeToOn Sensor
    entity_id = "sensor.myzone_time_to_on"
    state = hass.states.get(entity_id)
    assert state
    assert int(state.state) == 0

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-timetoOn"

    value = 20

    await hass.services.async_call(
        DOMAIN,
        "set_time_to",
        {ATTR_ENTITY_ID: [entity_id], ADVANTAGE_AIR_SET_COUNTDOWN_VALUE: value},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test First TimeToOff Sensor
    entity_id = "sensor.myzone_time_to_off"
    state = hass.states.get(entity_id)
    assert state
    assert int(state.state) == 10

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-timetoOff"

    value = 0
    await hass.services.async_call(
        DOMAIN,
        "set_time_to",
        {ATTR_ENTITY_ID: [entity_id], ADVANTAGE_AIR_SET_COUNTDOWN_VALUE: value},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test First Zone Vent Sensor
    entity_id = "sensor.myzone_zone_open_with_sensor_vent"
    state = hass.states.get(entity_id)
    assert state
    assert int(state.state) == 100

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z01-vent"

    # Test Second Zone Vent Sensor
    entity_id = "sensor.myzone_zone_closed_with_sensor_vent"
    state = hass.states.get(entity_id)
    assert state
    assert int(state.state) == 0

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z02-vent"

    # Test First Zone Signal Sensor
    entity_id = "sensor.myzone_zone_open_with_sensor_signal"
    state = hass.states.get(entity_id)
    assert state
    assert int(state.state) == 40

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z01-signal"

    # Test Second Zone Signal Sensor
    entity_id = "sensor.myzone_zone_closed_with_sensor_signal"
    state = hass.states.get(entity_id)
    assert state
    assert int(state.state) == 10

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z02-signal"