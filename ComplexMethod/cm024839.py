async def test_time_using_sensor(hass: HomeAssistant) -> None:
    """Test time conditions using sensor entities."""
    hass.states.async_set(
        "sensor.am",
        "2021-06-03 13:00:00.000000+00:00",  # 6 am local time
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )
    hass.states.async_set(
        "sensor.pm",
        "2020-06-01 01:00:00.000000+00:00",  # 6 pm local time
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )
    hass.states.async_set(
        "sensor.no_device_class",
        "2020-06-01 01:00:00.000000+00:00",
    )
    hass.states.async_set(
        "sensor.invalid_timestamp",
        "This is not a timestamp",
        {ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP},
    )

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=3),
    ):
        assert not condition.time(hass, after="sensor.am", before="sensor.pm")
        assert condition.time(hass, after="sensor.pm", before="sensor.am")

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=9),
    ):
        assert condition.time(hass, after="sensor.am", before="sensor.pm")
        assert not condition.time(hass, after="sensor.pm", before="sensor.am")

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=15),
    ):
        assert condition.time(hass, after="sensor.am", before="sensor.pm")
        assert not condition.time(hass, after="sensor.pm", before="sensor.am")

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=21),
    ):
        assert not condition.time(hass, after="sensor.am", before="sensor.pm")
        assert condition.time(hass, after="sensor.pm", before="sensor.am")

    # Trigger on PM time
    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=18, minute=0, second=0),
    ):
        assert condition.time(hass, after="sensor.pm", before="sensor.am")
        assert not condition.time(hass, after="sensor.am", before="sensor.pm")
        assert condition.time(hass, after="sensor.pm")
        assert not condition.time(hass, before="sensor.pm")

        # Even though valid, the device class is missing
        assert not condition.time(hass, after="sensor.no_device_class")
        assert not condition.time(hass, before="sensor.no_device_class")

    # Trigger on AM time
    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=6, minute=0, second=0),
    ):
        assert not condition.time(hass, after="sensor.pm", before="sensor.am")
        assert condition.time(hass, after="sensor.am", before="sensor.pm")
        assert condition.time(hass, after="sensor.am")
        assert not condition.time(hass, before="sensor.am")

    assert not condition.time(hass, after="sensor.invalid_timestamp")
    assert not condition.time(hass, before="sensor.invalid_timestamp")

    with pytest.raises(ConditionError):
        condition.time(hass, after="sensor.not_existing")

    with pytest.raises(ConditionError):
        condition.time(hass, before="sensor.not_existing")