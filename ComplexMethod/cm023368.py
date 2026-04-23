async def test_sensor_with_time_filtering(
    hass: HomeAssistant,
    mock_nsapi: AsyncMock,
) -> None:
    """Test that the time-based window filter correctly filters trips.

    This test verifies that:
    1. Trips BEFORE the configured time are filtered out
    2. Trips AT or AFTER the configured time are included
    3. The filtering is based on time-only (ignoring date)
    """
    # Create a config entry with a route that has time set to 16:00
    # Test frozen at: 2025-09-15 14:30 UTC = 16:30 Amsterdam time
    # The fixture includes trips at the following times:
    # 16:24/16:25 (trip 0) - FILTERED OUT (departed before 16:30 now)
    # 16:34/16:35 (trip 1) - INCLUDED (>= 16:00 configured time AND > 16:30 now)
    # With time=16:00, only future trips at or after 16:00 are included
    config_entry = MockConfigEntry(
        title=INTEGRATION_TITLE,
        data={CONF_API_KEY: API_KEY},
        domain=DOMAIN,
        subentries_data=[
            ConfigSubentryDataWithId(
                data={
                    CONF_NAME: "Afternoon commute",
                    CONF_FROM: "Ams",
                    CONF_TO: "Rot",
                    CONF_VIA: "Ht",
                    CONF_TIME: "16:00",
                },
                subentry_type=SUBENTRY_TYPE_ROUTE,
                title="Afternoon Route",
                unique_id=None,
                subentry_id="test_route_time_filter",
            ),
        ],
    )

    await setup_integration(hass, config_entry)
    await hass.async_block_till_done()

    # Should create sensors for the route
    sensor_states = hass.states.async_all("sensor")
    assert len(sensor_states) == 13

    # Find the actual departure time sensor and next departure sensor
    actual_departure_sensor = hass.states.get("sensor.afternoon_commute_departure")
    next_departure_sensor = hass.states.get("sensor.afternoon_commute_next_departure")

    assert actual_departure_sensor is not None, "Actual departure sensor not found"
    assert actual_departure_sensor.state != STATE_UNKNOWN

    # The sensor state is a UTC timestamp, convert it to Amsterdam time
    ams_tz = zoneinfo.ZoneInfo("Europe/Amsterdam")

    departure_dt = datetime.fromisoformat(actual_departure_sensor.state)
    departure_local = departure_dt.astimezone(ams_tz)

    hour = departure_local.hour
    minute = departure_local.minute
    # Verify first trip: is NOT before 16:00 (i.e., filtered trips are excluded)
    assert hour >= 16, (
        f"Expected first trip at or after 16:00 Amsterdam time, but got {hour}:{minute:02d}. "
        "This means trips before the configured time were NOT filtered out by the time window filter."
    )

    # Verify next trip also passes the filter
    assert next_departure_sensor is not None, "Next departure sensor not found"
    next_departure_dt = datetime.fromisoformat(next_departure_sensor.state)
    next_departure_local = next_departure_dt.astimezone(ams_tz)

    next_hour = next_departure_local.hour
    next_minute = next_departure_local.minute

    # Verify next trip is also at or after 16:00
    assert next_hour >= 16, (
        f"Expected next trip at or after 16:00 Amsterdam time, but got {next_hour}:{next_minute:02d}. "
        "This means the window filter is not applied consistently to all trips."
    )

    # Verify next trip is after the first trip
    assert (next_hour, next_minute) > (hour, minute), (
        f"Expected next trip ({next_hour}:{next_minute:02d}) to be after first trip ({hour}:{minute:02d})"
    )