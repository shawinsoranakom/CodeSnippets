async def test_off_delay(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test off_delay option."""
    # setup mocking rflink module
    event_callback, create, _, _ = await mock_rflink(hass, CONFIG, DOMAIN, monkeypatch)

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    events = []

    on_event = {"id": "test2", "command": "on"}

    @callback
    def listener(event):
        """Verify event got called."""
        events.append(event)

    hass.bus.async_listen(EVENT_STATE_CHANGED, listener)

    now = dt_util.utcnow()
    # fake time and turn on sensor
    future = now + timedelta(seconds=0)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        event_callback(on_event)
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test2")
    assert state.state == STATE_ON
    assert len(events) == 1

    # fake time and turn on sensor again
    future = now + timedelta(seconds=15)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        event_callback(on_event)
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test2")
    assert state.state == STATE_ON
    assert len(events) == 2

    # fake time and verify sensor still on (de-bounce)
    future = now + timedelta(seconds=35)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test2")
    assert state.state == STATE_ON
    assert len(events) == 2

    # fake time and verify sensor is off
    future = now + timedelta(seconds=45)
    with freeze_time(future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.test2")
    assert state.state == STATE_OFF
    assert len(events) == 3