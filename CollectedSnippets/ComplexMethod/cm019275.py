async def test_sensor_state_class_no_uom_not_available(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test when input sensors drops unit of measurement."""

    # If we have a valid unit of measurement from all input sensors
    # the group sensor will go unknown in the case any input sensor
    # drops the unit of measurement and log a warning.

    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": "test_sum",
            "type": "sum",
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id_sum_sensor",
        }
    }

    entity_ids = config["sensor"]["entities"]

    input_attributes = {
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": PERCENTAGE,
    }

    hass.states.async_set(entity_ids[0], str(VALUES[0]), input_attributes)
    hass.states.async_set(entity_ids[1], str(VALUES[1]), input_attributes)
    hass.states.async_set(entity_ids[2], str(VALUES[2]), input_attributes)
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == str(sum(VALUES))
    assert state.attributes.get("state_class") == "measurement"
    assert state.attributes.get("unit_of_measurement") == "%"

    assert (
        "Unable to use state. Only entities with correct unit of measurement is"
        " supported"
    ) not in caplog.text

    # sensor.test_3 drops the unit of measurement
    hass.states.async_set(
        entity_ids[2],
        str(VALUES[2]),
        {
            "state_class": SensorStateClass.MEASUREMENT,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("state_class") == "measurement"
    assert state.attributes.get("unit_of_measurement") is None

    assert (
        "Unable to use state. Only entities with correct unit of measurement is"
        " supported, entity sensor.test_3, value 15.3 with"
        " device class None and unit of measurement None excluded from calculation"
        " in sensor.test_sum"
    ) in caplog.text