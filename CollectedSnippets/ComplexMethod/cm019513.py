async def test_sensors_attributes_pro(hass: HomeAssistant, canary) -> None:
    """Test the creation and values of the sensors attributes for Canary Pro."""

    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.59"),
    ]

    with patch("homeassistant.components.canary.PLATFORMS", ["sensor"]):
        await init_integration(hass)

    entity_id = "sensor.dining_room_home_dining_room_air_quality"
    state1 = hass.states.get(entity_id)
    assert state1
    assert state1.state == "0.59"
    assert state1.attributes[ATTR_AIR_QUALITY] == STATE_AIR_QUALITY_ABNORMAL

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.4"),
    ]

    future = utcnow() + timedelta(seconds=30)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done(wait_background_tasks=True)

    state2 = hass.states.get(entity_id)
    assert state2
    assert state2.state == "0.4"
    assert state2.attributes[ATTR_AIR_QUALITY] == STATE_AIR_QUALITY_VERY_ABNORMAL

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "1.0"),
    ]

    future += timedelta(seconds=30)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done(wait_background_tasks=True)

    state3 = hass.states.get(entity_id)
    assert state3
    assert state3.state == "1.0"
    assert state3.attributes[ATTR_AIR_QUALITY] == STATE_AIR_QUALITY_NORMAL