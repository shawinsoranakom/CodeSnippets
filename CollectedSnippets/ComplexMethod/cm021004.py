async def test_to_midnight(
    hass: HomeAssistant,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    caplog: pytest.LogCaptureFixture,
    schedule: list[dict[str, str]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test time range allow to 24:00."""
    freezer.move_to("2022-08-30 13:20:00-07:00")

    assert await schedule_setup(
        config={
            DOMAIN: {
                "from_yaml": {
                    CONF_NAME: "from yaml",
                    CONF_ICON: "mdi:party-popper",
                    CONF_SUNDAY: schedule,
                }
            }
        },
        items=[],
    )

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-04T00:00:00-07:00"

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
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-09-11T00:00:00-07:00"