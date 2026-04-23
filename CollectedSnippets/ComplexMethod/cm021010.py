async def test_schedule_state_trigger_back_to_back(
    hass: HomeAssistant,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that the schedule state trigger fires when transitioning between two back-to-back schedule blocks."""
    calls: list[str] = []
    freezer.move_to("2022-08-30 13:20:00-07:00")
    entity_id = "schedule.from_yaml"

    assert await schedule_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    CONF_NAME: "from yaml",
                    CONF_ICON: "mdi:party-popper",
                    CONF_SUNDAY: [
                        {CONF_FROM: "22:00:00", CONF_TO: "22:30:00"},
                        {CONF_FROM: "22:30:00", CONF_TO: "23:00:00"},
                    ],
                }
            }
        },
        items=[],
    )

    await arm_trigger(
        hass,
        "schedule.turned_on",
        {},
        {"entity_id": [entity_id]},
        calls,
    )

    # initial state
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T22:00:00-07:00"

    # move time into first block
    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T22:30:00-07:00"

    assert len(calls) == 1
    assert calls[0] == entity_id
    calls.clear()

    # move time into second block (back-to-back)
    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T23:00:00-07:00"

    assert len(calls) == 1
    assert calls[0] == entity_id
    calls.clear()

    # move time to after second block to ensure it turns off
    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-11T22:00:00-07:00"

    assert len(calls) == 0