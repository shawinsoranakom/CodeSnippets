async def test_availability_forecast(
    hass: HomeAssistant,
    exception: Exception,
    mock_accuweather_client: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    entity_id = "sensor.home_hours_of_sun_day_2"

    await init_integration(hass)

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "5.7"

    mock_accuweather_client.async_get_daily_forecast.side_effect = exception

    freezer.tick(UPDATE_INTERVAL_DAILY_FORECAST)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_accuweather_client.async_get_daily_forecast.side_effect = None

    freezer.tick(UPDATE_INTERVAL_DAILY_FORECAST)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "5.7"