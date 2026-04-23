async def test_availability(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_google_weather_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    entity_id = "sensor.home_temperature"
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "13.7"

    mock_google_weather_api.async_get_current_conditions.side_effect = (
        GoogleWeatherApiError()
    )

    freezer.tick(timedelta(minutes=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_google_weather_api.async_get_current_conditions.side_effect = None

    freezer.tick(timedelta(minutes=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "13.7"
    mock_google_weather_api.async_get_current_conditions.assert_called_with(
        latitude=10.1, longitude=20.1
    )