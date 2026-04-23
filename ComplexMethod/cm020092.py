async def test_binary_sensor_counter(
    hass: HomeAssistant,
    knx: KNXTestKit,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test KNX binary_sensor with context timeout."""
    context_timeout = 1

    await knx.setup_integration(
        {
            BinarySensorSchema.PLATFORM: [
                {
                    CONF_NAME: "test",
                    CONF_STATE_ADDRESS: "2/2/2",
                    CONF_CONTEXT_TIMEOUT: context_timeout,
                    CONF_SYNC_STATE: False,
                },
            ]
        }
    )
    events = async_capture_events(hass, "state_changed")

    # receive initial ON telegram
    await knx.receive_write("2/2/2", True)
    # no change yet - still in 1 sec context (additional async_block_till_done needed for time change)
    assert len(events) == 0
    state = hass.states.get("binary_sensor.test")
    assert state.state is STATE_OFF
    assert state.attributes.get("counter") == 0
    freezer.tick(timedelta(seconds=context_timeout))
    async_fire_time_changed(hass)
    await knx.xknx.task_registry.block_till_done()
    # state changed twice after context timeout - once to ON with counter 1 and once to counter 0
    state = hass.states.get("binary_sensor.test")
    assert state.state is STATE_ON
    assert state.attributes.get("counter") == 0
    assert len(events) == 2
    event = events.pop(0).data
    assert event.get("new_state").attributes.get("counter") == 1
    assert event.get("old_state").attributes.get("counter") == 0
    event = events.pop(0).data
    assert event.get("new_state").attributes.get("counter") == 0
    assert event.get("old_state").attributes.get("counter") == 1

    # receive 2 telegrams in context
    await knx.receive_write("2/2/2", True)
    await knx.receive_write("2/2/2", True)
    assert len(events) == 0
    state = hass.states.get("binary_sensor.test")
    assert state.state is STATE_ON
    assert state.attributes.get("counter") == 0
    freezer.tick(timedelta(seconds=context_timeout))
    async_fire_time_changed(hass)
    await knx.xknx.task_registry.block_till_done()
    state = hass.states.get("binary_sensor.test")
    assert state.state is STATE_ON
    assert state.attributes.get("counter") == 0
    assert len(events) == 2
    event = events.pop(0).data
    assert event.get("new_state").attributes.get("counter") == 2
    assert event.get("old_state").attributes.get("counter") == 0
    event = events.pop(0).data
    assert event.get("new_state").attributes.get("counter") == 0
    assert event.get("old_state").attributes.get("counter") == 2