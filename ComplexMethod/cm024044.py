async def test_availability(
    hass: HomeAssistant,
    mock_accuweather_client: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    entity_id = "weather.home"
    await init_integration(hass)

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "sunny"

    mock_accuweather_client.async_get_current_conditions.side_effect = ConnectionError

    freezer.tick(UPDATE_INTERVAL_DAILY_FORECAST)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_accuweather_client.async_get_current_conditions.side_effect = None

    freezer.tick(UPDATE_INTERVAL_DAILY_FORECAST)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "sunny"