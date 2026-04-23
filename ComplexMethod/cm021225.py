async def test_set_datetime_4(hass: HomeAssistant) -> None:
    """Test set_datetime method using timestamp 0."""
    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test_datetime": {"has_time": True, "has_date": True}}}
    )

    entity_id = "input_datetime.test_datetime"

    dt_obj = datetime.datetime(
        1969, 12, 31, 16, 00, 00, tzinfo=dt_util.get_time_zone(hass.config.time_zone)
    )

    await async_set_timestamp(hass, entity_id, 0)

    state = hass.states.get(entity_id)
    assert state.state == dt_obj.strftime(FORMAT_DATETIME)
    assert state.attributes["has_time"]
    assert state.attributes["has_date"]

    assert state.attributes["year"] == 1969
    assert state.attributes["month"] == 12
    assert state.attributes["day"] == 31
    assert state.attributes["hour"] == 16
    assert state.attributes["minute"] == 00
    assert state.attributes["second"] == 0
    assert state.attributes["timestamp"] == 0