async def test_timestamp(hass: HomeAssistant) -> None:
    """Test timestamp."""
    await hass.config.async_set_time_zone("America/Los_Angeles")

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test_datetime_initial_with_tz": {
                    "has_time": True,
                    "has_date": True,
                    "initial": "2020-12-13 10:00:00+01:00",
                },
                "test_datetime_initial_without_tz": {
                    "has_time": True,
                    "has_date": True,
                    "initial": "2020-12-13 10:00:00",
                },
                "test_time_initial": {
                    "has_time": True,
                    "has_date": False,
                    "initial": "10:00:00",
                },
            }
        },
    )

    # initial has been converted to the set timezone
    state_with_tz = hass.states.get("input_datetime.test_datetime_initial_with_tz")
    assert state_with_tz is not None
    # Timezone LA is UTC-8 => timestamp carries +01:00 => delta is -9 => 10:00 - 09:00 => 01:00
    assert state_with_tz.state == "2020-12-13 01:00:00"
    assert (
        dt_util.as_local(
            dt_util.utc_from_timestamp(state_with_tz.attributes[ATTR_TIMESTAMP])
        ).strftime(FORMAT_DATETIME)
        == "2020-12-13 01:00:00"
    )

    # initial has been interpreted as being part of set timezone
    state_without_tz = hass.states.get(
        "input_datetime.test_datetime_initial_without_tz"
    )
    assert state_without_tz is not None
    assert state_without_tz.state == "2020-12-13 10:00:00"
    # Timezone LA is UTC-8 => timestamp has no zone (= assumed local) => delta to UTC is +8 => 10:00 + 08:00 => 18:00
    assert (
        dt_util.utc_from_timestamp(
            state_without_tz.attributes[ATTR_TIMESTAMP]
        ).strftime(FORMAT_DATETIME)
        == "2020-12-13 18:00:00"
    )
    assert (
        dt_util.as_local(
            dt_util.utc_from_timestamp(state_without_tz.attributes[ATTR_TIMESTAMP])
        ).strftime(FORMAT_DATETIME)
        == "2020-12-13 10:00:00"
    )
    # Use datetime.datetime.fromtimestamp
    assert (
        dt_util.as_local(
            datetime.datetime.fromtimestamp(
                state_without_tz.attributes[ATTR_TIMESTAMP], datetime.UTC
            )
        ).strftime(FORMAT_DATETIME)
        == "2020-12-13 10:00:00"
    )

    # Test initial time sets timestamp correctly.
    state_time = hass.states.get("input_datetime.test_time_initial")
    assert state_time is not None
    assert state_time.state == "10:00:00"
    assert state_time.attributes[ATTR_TIMESTAMP] == 10 * 60 * 60

    # Test that setting the timestamp of an entity works.
    await hass.services.async_call(
        DOMAIN,
        "set_datetime",
        {
            ATTR_ENTITY_ID: "input_datetime.test_datetime_initial_with_tz",
            ATTR_TIMESTAMP: state_without_tz.attributes[ATTR_TIMESTAMP],
        },
        blocking=True,
    )
    state_with_tz_updated = hass.states.get(
        "input_datetime.test_datetime_initial_with_tz"
    )
    assert state_with_tz_updated.state == "2020-12-13 10:00:00"
    assert (
        state_with_tz_updated.attributes[ATTR_TIMESTAMP]
        == state_without_tz.attributes[ATTR_TIMESTAMP]
    )