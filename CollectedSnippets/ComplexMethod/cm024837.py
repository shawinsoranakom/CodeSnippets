async def test_time_using_input_datetime(hass: HomeAssistant) -> None:
    """Test time conditions using input_datetime entities."""
    await async_setup_component(
        hass,
        "input_datetime",
        {
            "input_datetime": {
                "am": {"has_date": True, "has_time": True},
                "pm": {"has_date": True, "has_time": True},
            }
        },
    )

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.am",
            "datetime": str(
                dt_util.now()
                .replace(hour=6, minute=0, second=0, microsecond=0)
                .replace(tzinfo=None)
            ),
        },
        blocking=True,
    )

    await hass.services.async_call(
        "input_datetime",
        "set_datetime",
        {
            "entity_id": "input_datetime.pm",
            "datetime": str(
                dt_util.now()
                .replace(hour=18, minute=0, second=0, microsecond=0)
                .replace(tzinfo=None)
            ),
        },
        blocking=True,
    )

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=3),
    ):
        assert not condition.time(
            hass, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(
            hass, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=9),
    ):
        assert condition.time(
            hass, after="input_datetime.am", before="input_datetime.pm"
        )
        assert not condition.time(
            hass, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=15),
    ):
        assert condition.time(
            hass, after="input_datetime.am", before="input_datetime.pm"
        )
        assert not condition.time(
            hass, after="input_datetime.pm", before="input_datetime.am"
        )

    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=21),
    ):
        assert not condition.time(
            hass, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(
            hass, after="input_datetime.pm", before="input_datetime.am"
        )

    # Trigger on PM time
    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=18, minute=0, second=0),
    ):
        assert condition.time(
            hass, after="input_datetime.pm", before="input_datetime.am"
        )
        assert not condition.time(
            hass, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(hass, after="input_datetime.pm")
        assert not condition.time(hass, before="input_datetime.pm")

    # Trigger on AM time
    with patch(
        "homeassistant.helpers.condition.dt_util.now",
        return_value=dt_util.now().replace(hour=6, minute=0, second=0),
    ):
        assert not condition.time(
            hass, after="input_datetime.pm", before="input_datetime.am"
        )
        assert condition.time(
            hass, after="input_datetime.am", before="input_datetime.pm"
        )
        assert condition.time(hass, after="input_datetime.am")
        assert not condition.time(hass, before="input_datetime.am")

    with pytest.raises(ConditionError):
        condition.time(hass, after="input_datetime.not_existing")

    with pytest.raises(ConditionError):
        condition.time(hass, before="input_datetime.not_existing")