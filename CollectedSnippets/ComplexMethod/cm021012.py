async def test_sensor(
    hass: HomeAssistant,
    mode,
    icon,
    traffic_mode,
    arrival_time,
    departure_time,
) -> None:
    """Test that sensor works."""
    hass.set_state(CoreState.not_running)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456789",
        data={
            CONF_ORIGIN_LATITUDE: float(ORIGIN_LATITUDE),
            CONF_ORIGIN_LONGITUDE: float(ORIGIN_LONGITUDE),
            CONF_DESTINATION_LATITUDE: float(DESTINATION_LATITUDE),
            CONF_DESTINATION_LONGITUDE: float(DESTINATION_LONGITUDE),
            CONF_API_KEY: API_KEY,
            CONF_MODE: mode,
            CONF_NAME: "test",
        },
        options={
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_TRAFFIC_MODE: traffic_mode,
            CONF_ARRIVAL_TIME: arrival_time,
            CONF_DEPARTURE_TIME: departure_time,
        },
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    duration = hass.states.get("sensor.test_duration")
    assert duration.attributes.get("unit_of_measurement") == UnitOfTime.MINUTES
    assert duration.attributes.get(ATTR_ICON) == icon
    assert duration.state == "26.1833333333333"

    assert float(hass.states.get("sensor.test_distance").state) == pytest.approx(13.682)
    assert hass.states.get("sensor.test_duration_in_traffic").state == "29.6"
    assert hass.states.get("sensor.test_origin").state == "22nd St NW"
    assert (
        hass.states.get("sensor.test_origin").attributes.get(ATTR_LATITUDE)
        == "38.8999937"
    )
    assert (
        hass.states.get("sensor.test_origin").attributes.get(ATTR_LONGITUDE)
        == "-77.0479682"
    )

    assert hass.states.get("sensor.test_destination").state == "Service Rd S"
    assert (
        hass.states.get("sensor.test_destination").attributes.get(ATTR_LATITUDE)
        == "38.99997"
    )
    assert (
        hass.states.get("sensor.test_destination").attributes.get(ATTR_LONGITUDE)
        == "-77.10014"
    )