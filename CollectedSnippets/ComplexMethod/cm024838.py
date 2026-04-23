async def test_time_using_time(hass: HomeAssistant) -> None:
    """Test time conditions using time entities."""
    hass.states.async_set(
        "time.am",
        "06:00:00",  # 6 am local time
    )
    hass.states.async_set(
        "time.pm",
        "18:00:00",  # 6 pm local time
    )
    hass.states.async_set(
        "time.unknown_state",
        STATE_UNKNOWN,
    )
    hass.states.async_set(
        "time.unavailable_state",
        STATE_UNAVAILABLE,
    )

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=3),
    ):
        assert not condition.time(hass, after="time.am", before="time.pm")
        assert condition.time(hass, after="time.pm", before="time.am")

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=9),
    ):
        assert condition.time(hass, after="time.am", before="time.pm")
        assert not condition.time(hass, after="time.pm", before="time.am")

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=15),
    ):
        assert condition.time(hass, after="time.am", before="time.pm")
        assert not condition.time(hass, after="time.pm", before="time.am")

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=21),
    ):
        assert not condition.time(hass, after="time.am", before="time.pm")
        assert condition.time(hass, after="time.pm", before="time.am")

    # Trigger on PM time
    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=18, minute=0, second=0),
    ):
        assert condition.time(hass, after="time.pm", before="time.am")
        assert not condition.time(hass, after="time.am", before="time.pm")
        assert condition.time(hass, after="time.pm")
        assert not condition.time(hass, before="time.pm")

    # Trigger on AM time
    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=6, minute=0, second=0),
    ):
        assert not condition.time(hass, after="time.pm", before="time.am")
        assert condition.time(hass, after="time.am", before="time.pm")
        assert condition.time(hass, after="time.am")
        assert not condition.time(hass, before="time.am")

    assert not condition.time(hass, after="time.unknown_state")
    assert not condition.time(hass, before="time.unavailable_state")

    with pytest.raises(ConditionError):
        condition.time(hass, after="time.not_existing")

    with pytest.raises(ConditionError):
        condition.time(hass, before="time.not_existing")