async def test_sensor_calculated_properties_not_convertible_device_class(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the sensor calculating device_class, state_class and unit of measurement when device class not convertible."""
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

    hass.states.async_set(
        entity_ids[0],
        str(VALUES[0]),
        {
            "device_class": SensorDeviceClass.HUMIDITY,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": PERCENTAGE,
        },
    )
    hass.states.async_set(
        entity_ids[1],
        str(VALUES[1]),
        {
            "device_class": SensorDeviceClass.HUMIDITY,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": PERCENTAGE,
        },
    )
    hass.states.async_set(
        entity_ids[2],
        str(VALUES[2]),
        {
            "device_class": SensorDeviceClass.HUMIDITY,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": PERCENTAGE,
        },
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == str(sum(VALUES))
    assert state.attributes.get("device_class") == "humidity"
    assert state.attributes.get("state_class") == "measurement"
    assert state.attributes.get("unit_of_measurement") == "%"

    assert (
        "Unable to use state. Only entities with correct unit of measurement is"
        " supported"
    ) not in caplog.text

    hass.states.async_set(
        entity_ids[2],
        str(VALUES[2]),
        {
            "device_class": SensorDeviceClass.HUMIDITY,
            "state_class": SensorStateClass.MEASUREMENT,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("device_class") == "humidity"
    assert state.attributes.get("state_class") == "measurement"
    assert state.attributes.get("unit_of_measurement") is None

    assert (
        "Unable to use state. Only entities with correct unit of measurement is"
        " supported, entity sensor.test_3, value 15.3 with"
        " device class humidity and unit of measurement None excluded from calculation"
        " in sensor.test_sum"
    ) in caplog.text