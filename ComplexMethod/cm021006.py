async def test_schedule_updates(
    hass: HomeAssistant,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the schedule updates when time changes."""
    freezer.move_to("2022-08-10 20:10:00-07:00")
    assert await schedule_setup()

    state = hass.states.get(f"{DOMAIN}.from_storage")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-08-12T17:00:00-07:00"

    freezer.move_to(state.attributes[ATTR_NEXT_EVENT])
    async_fire_time_changed(hass)

    state = hass.states.get(f"{DOMAIN}.from_storage")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_NEXT_EVENT].isoformat() == "2022-08-12T23:59:59-07:00"