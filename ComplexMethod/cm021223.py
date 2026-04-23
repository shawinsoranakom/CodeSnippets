async def test_set_datetime_2(hass: HomeAssistant) -> None:
    """Test set_datetime method using datetime."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(
        2017, 9, 7, 19, 46, 30, tzinfo=dt_util.get_time_zone(hass.config.time_zone)
    )

    await async_set_datetime(hass, entity_id, dt_obj)

    state = hass.states.get(entity_id)
    assert state.state == dt_obj.strftime(FORMAT_DATETIME)
    assert state.attributes["has_time"]
    assert state.attributes["has_date"]

    assert state.attributes["year"] == 2017
    assert state.attributes["month"] == 9
    assert state.attributes["day"] == 7
    assert state.attributes["hour"] == 19
    assert state.attributes["minute"] == 46
    assert state.attributes["second"] == 30
    assert state.attributes["timestamp"] == dt_obj.timestamp()