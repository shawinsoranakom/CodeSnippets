async def test_time_window(hass: HomeAssistant) -> None:
    """Test time condition windows."""
    sixam = "06:00:00"
    sixpm = "18:00:00"

    config1 = {
        "alias": "Time Cond",
        "condition": "time",
        "after": sixam,
        "before": sixpm,
    }
    config1 = cv.CONDITION_SCHEMA(config1)
    config1 = await condition.async_validate_condition_config(hass, config1)
    config2 = {
        "alias": "Time Cond",
        "condition": "time",
        "after": sixpm,
        "before": sixam,
    }
    config2 = cv.CONDITION_SCHEMA(config2)
    config2 = await condition.async_validate_condition_config(hass, config2)
    test1 = await condition.async_from_config(hass, config1)
    test2 = await condition.async_from_config(hass, config2)

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=3),
    ):
        assert not test1(hass)
        assert test2(hass)

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=9),
    ):
        assert test1(hass)
        assert not test2(hass)

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=15),
    ):
        assert test1(hass)
        assert not test2(hass)

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=21),
    ):
        assert not test1(hass)
        assert test2(hass)