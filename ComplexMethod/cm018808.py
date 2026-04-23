async def test_attributes_remains(recorder_mock: Recorder, hass: HomeAssistant) -> None:
    """Test attributes are always present."""
    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    current_time = dt_util.utcnow()
    with freeze_time(current_time) as freezer:
        assert await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "max_age": {"seconds": 10},
                    },
                ]
            },
        )
        await hass.async_block_till_done()

        state = hass.states.get("sensor.test")
        assert state is not None
        assert state.state == str(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2))
        assert state.attributes == {
            "age_coverage_ratio": 0.0,
            "friendly_name": "test",
            "icon": "mdi:calculator",
            "source_value_valid": True,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "°C",
        }

        freezer.move_to(current_time + timedelta(minutes=1))
        async_fire_time_changed(hass)

        state = hass.states.get("sensor.test")
        assert state is not None
        assert state.state == STATE_UNKNOWN
        assert state.attributes == {
            "age_coverage_ratio": 0,
            "friendly_name": "test",
            "icon": "mdi:calculator",
            "source_value_valid": True,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "°C",
        }