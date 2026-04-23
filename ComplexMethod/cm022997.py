async def test_icons(hass: HomeAssistant) -> None:
    """Test attributes of sensors."""
    for option in OPTION_TYPES:
        await load_int(hass, option)

    state = hass.states.get("sensor.time")
    assert state.attributes["icon"] == "mdi:clock"
    state = hass.states.get("sensor.date")
    assert state.attributes["icon"] == "mdi:calendar"
    state = hass.states.get("sensor.time_utc")
    assert state.attributes["icon"] == "mdi:clock"
    state = hass.states.get("sensor.date_time")
    assert state.attributes["icon"] == "mdi:calendar-clock"
    state = hass.states.get("sensor.date_time_utc")
    assert state.attributes["icon"] == "mdi:calendar-clock"
    state = hass.states.get("sensor.date_time_iso")
    assert state.attributes["icon"] == "mdi:calendar-clock"