async def test_template_trigger_delay_on_and_auto_off(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test binary sensor template with delay_on, auto_off, and multiple triggers."""
    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    assert state.state == STATE_UNKNOWN

    context = Context()
    hass.bus.async_fire("test_event", {"beer": 2}, context=context)
    await hass.async_block_till_done()

    # State should still be unknown
    state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
    assert state.state == STATE_UNKNOWN
    last_state = STATE_UNKNOWN

    for _ in range(5):
        # Now wait and trigger again to test that the 2 second on_delay is not recreated
        freezer.tick(timedelta(seconds=1))
        hass.bus.async_fire("test_event", {"beer": 2}, context=context)
        await hass.async_block_till_done()

        state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
        assert state.state == last_state

        # Now wait for the on delay
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
        assert state.state == STATE_ON

        # Now wait for the auto-off
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
        assert state.state == STATE_OFF

        # Now wait to trigger again
        freezer.tick(timedelta(seconds=1))
        hass.bus.async_fire("test_event", {"beer": 2}, context=context)
        await hass.async_block_till_done()

        # State should still be off
        state = hass.states.get(TEST_BINARY_SENSOR.entity_id)
        assert state.state == STATE_OFF

        last_state = STATE_OFF