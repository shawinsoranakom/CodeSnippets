async def test_coordinator_with_errors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    setup_integration: Callable[[], Awaitable[bool]],
    mock_api: VolvoCarsApi,
) -> None:
    """Test coordinator with errors."""
    assert await setup_integration()

    sensor_id = "sensor.volvo_xc40_odometer"
    interval = timedelta(minutes=VERY_SLOW_INTERVAL)
    value = {"odometer": VolvoCarsValueField(value=30000, unit="km")}
    mock_method: AsyncMock = mock_api.async_get_odometer

    state = hass.states.get(sensor_id)
    assert state.state == "30000"

    configure_mock(mock_method, side_effect=VolvoApiException())
    freezer.tick(interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_method.call_count == 1
    state = hass.states.get(sensor_id)
    assert state.state == STATE_UNAVAILABLE

    configure_mock(mock_method, return_value=value)
    freezer.tick(interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_method.call_count == 1
    state = hass.states.get(sensor_id)
    assert state.state == "30000"

    configure_mock(mock_method, side_effect=Exception())
    freezer.tick(interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_method.call_count == 1
    state = hass.states.get(sensor_id)
    assert state.state == STATE_UNAVAILABLE

    configure_mock(mock_method, return_value=value)
    freezer.tick(interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_method.call_count == 1
    state = hass.states.get(sensor_id)
    assert state.state == "30000"

    configure_mock(mock_method, side_effect=VolvoAuthException())
    freezer.tick(interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_method.call_count == 1
    state = hass.states.get(sensor_id)
    assert state.state == STATE_UNAVAILABLE