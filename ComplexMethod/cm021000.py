async def test_events_one_day(
    hass: HomeAssistant,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test events only during one day of the week."""
    freezer.move_to("2022-08-30 13:20:00-07:00")

    assert await schedule_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    CONF_NAME: "from yaml",
                    CONF_ICON: "mdi:party-popper",
                    CONF_SUNDAY: {CONF_FROM: "07:00:00", CONF_TO: "11:00:00"},
                }
            }
        },
        items=[],
    )

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T07:00:00-07:00"

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T11:00:00-07:00"

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-11T07:00:00-07:00"