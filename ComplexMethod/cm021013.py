async def test_restore_state(hass: HomeAssistant) -> None:
    """Test sensor restore state."""
    # Home assistant is not running yet
    hass.set_state(CoreState.not_running)
    last_reset = "2022-11-29T00:00:00.000000+00:00"
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(
                    "sensor.test_duration",
                    "1234",
                    attributes={
                        ATTR_LAST_RESET: last_reset,
                        ATTR_UNIT_OF_MEASUREMENT: UnitOfTime.SECONDS,
                        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
                    },
                ),
                {
                    "native_value": 1234,
                    "native_unit_of_measurement": UnitOfTime.SECONDS,
                    "icon": "mdi:car",
                    "last_reset": last_reset,
                },
            ),
            (
                State(
                    "sensor.test_duration_in_traffic",
                    "5678",
                    attributes={
                        ATTR_LAST_RESET: last_reset,
                        ATTR_UNIT_OF_MEASUREMENT: UnitOfTime.SECONDS,
                        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
                    },
                ),
                {
                    "native_value": 5678,
                    "native_unit_of_measurement": UnitOfTime.SECONDS,
                    "icon": "mdi:car",
                    "last_reset": last_reset,
                },
            ),
            (
                State(
                    "sensor.test_distance",
                    "123",
                    attributes={
                        ATTR_LAST_RESET: last_reset,
                        ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
                    },
                ),
                {
                    "native_value": 123,
                    "native_unit_of_measurement": UnitOfLength.KILOMETERS,
                    "icon": "mdi:car",
                    "last_reset": last_reset,
                },
            ),
            (
                State(
                    "sensor.test_origin",
                    "Origin Address 1",
                    attributes={
                        ATTR_LAST_RESET: last_reset,
                        ATTR_LATITUDE: ORIGIN_LATITUDE,
                        ATTR_LONGITUDE: ORIGIN_LONGITUDE,
                    },
                ),
                {
                    "native_value": "Origin Address 1",
                    "native_unit_of_measurement": None,
                    ATTR_LATITUDE: ORIGIN_LATITUDE,
                    ATTR_LONGITUDE: ORIGIN_LONGITUDE,
                    "icon": "mdi:store-marker",
                    "last_reset": last_reset,
                },
            ),
            (
                State(
                    "sensor.test_destination",
                    "Destination Address 1",
                    attributes={
                        ATTR_LAST_RESET: last_reset,
                        ATTR_LATITUDE: DESTINATION_LATITUDE,
                        ATTR_LONGITUDE: DESTINATION_LONGITUDE,
                    },
                ),
                {
                    "native_value": "Destination Address 1",
                    "native_unit_of_measurement": None,
                    "icon": "mdi:store-marker",
                    "last_reset": last_reset,
                },
            ),
        ],
    )

    # create and add entry
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data=DEFAULT_CONFIG,
        options=DEFAULT_OPTIONS,
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
    )
    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    # restore from cache
    state = hass.states.get("sensor.test_duration")
    assert state.state == "20.5666666666667"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTime.MINUTES
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.test_duration_in_traffic")
    assert state.state == "94.6333333333333"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTime.MINUTES
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.test_distance")
    assert state.state == "123"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfLength.KILOMETERS
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.test_origin")
    assert state.state == "Origin Address 1"

    state = hass.states.get("sensor.test_destination")
    assert state.state == "Destination Address 1"