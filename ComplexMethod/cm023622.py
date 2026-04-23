async def test_refresh_weather_forecast_retry(
    hass: HomeAssistant,
    error: Exception,
    load_int: MockConfigEntry,
    mock_client: SMHIPointForecast,
    mock_fire_client: SMHIFirePointForecast,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the refresh weather forecast function."""

    mock_client.async_get_daily_forecast.side_effect = error

    freezer.tick(timedelta(minutes=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)

    assert state
    assert state.name == "Test"
    assert state.state == STATE_UNAVAILABLE
    assert mock_client.async_get_daily_forecast.call_count == 2

    freezer.tick(timedelta(minutes=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_UNAVAILABLE
    assert mock_client.async_get_daily_forecast.call_count == 3