async def test_no_departures(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_israelrail: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test handling when there are no departures available."""
    await init_integration(hass, mock_config_entry)
    assert len(hass.states.async_entity_ids()) == 6

    # Simulate no departures (e.g., after-hours)
    mock_israelrail.query.return_value = []

    await goto_future(hass, freezer)

    # All sensors should still exist
    assert len(hass.states.async_entity_ids()) == 6

    # Departure sensors should have unknown state (None)
    departure_sensor = hass.states.get("sensor.mock_title_departure")
    assert departure_sensor.state == STATE_UNKNOWN

    departure_sensor_1 = hass.states.get("sensor.mock_title_departure_1")
    assert departure_sensor_1.state == STATE_UNKNOWN

    departure_sensor_2 = hass.states.get("sensor.mock_title_departure_2")
    assert departure_sensor_2.state == STATE_UNKNOWN

    # Non-departure sensors (platform, trains, train_number) also access index 0
    # and should have unknown state when no departures available
    platform_sensor = hass.states.get("sensor.mock_title_platform")
    assert platform_sensor.state == STATE_UNKNOWN

    trains_sensor = hass.states.get("sensor.mock_title_trains")
    assert trains_sensor.state == STATE_UNKNOWN

    train_number_sensor = hass.states.get("sensor.mock_title_train_number")
    assert train_number_sensor.state == STATE_UNKNOWN