async def test_adjacent_cross_midnight(
    hass: HomeAssistant,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test adjacent events don't toggle on->off->on."""
    freezer.move_to("2022-08-30 13:20:00-07:00")

    assert await schedule_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    CONF_NAME: "from yaml",
                    CONF_ICON: "mdi:party-popper",
                    CONF_SUNDAY: {CONF_FROM: "23:00:00", CONF_TO: "24:00:00"},
                    CONF_MONDAY: {CONF_FROM: "00:00:00", CONF_TO: "01:00:00"},
                }
            }
        },
        items=[],
    )

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T23:00:00-07:00"

    state_changes = async_capture_events(hass, EVENT_STATE_CHANGED)

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-05T00:00:00-07:00"

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-05T01:00:00-07:00"

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-11T23:00:00-07:00"

    await hass.async_block_till_done()
    assert len(state_changes) == 3
    for event in state_changes[:-1]:
        assert event.data["new_state"].state == STATE_ON
    assert state_changes[2].data["new_state"].state == STATE_OFF