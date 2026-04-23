async def test_sensor_different_attributes_ignore_non_numeric(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the sensor handles calculating attributes when using ignore_non_numeric."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": "test_sum",
            "type": "sum",
            "ignore_non_numeric": True,
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id_sum_sensor",
        }
    }

    entity_ids = config["sensor"]["entities"]

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("state_class") is None
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("unit_of_measurement") is None

    test_cases = [
        {
            "entity": entity_ids[0],
            "value": str(VALUES[0]),
            "attributes": {
                "state_class": SensorStateClass.MEASUREMENT,
                "unit_of_measurement": PERCENTAGE,
            },
            "expected_state": str(float(VALUES[0])),
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_device_class": None,
            "expected_unit_of_measurement": PERCENTAGE,
        },
        {
            "entity": entity_ids[1],
            "value": str(VALUES[1]),
            "attributes": {
                "state_class": SensorStateClass.MEASUREMENT,
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
            },
            "expected_state": str(float(sum([VALUES[0], VALUES[1]]))),
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_device_class": None,
            "expected_unit_of_measurement": PERCENTAGE,
        },
        {
            "entity": entity_ids[2],
            "value": str(VALUES[2]),
            "attributes": {
                "state_class": SensorStateClass.MEASUREMENT,
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
            },
            "expected_state": str(float(sum(VALUES))),
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_device_class": None,
            "expected_unit_of_measurement": None,
        },
        {
            "entity": entity_ids[2],
            "value": str(VALUES[2]),
            "attributes": {
                "state_class": SensorStateClass.MEASUREMENT,
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
            },
            "expected_state": str(float(sum(VALUES))),
            "expected_state_class": SensorStateClass.MEASUREMENT,
            # One sensor does not have a device class
            "expected_device_class": None,
            "expected_unit_of_measurement": PERCENTAGE,
        },
        {
            "entity": entity_ids[0],
            "value": str(VALUES[0]),
            "attributes": {
                "state_class": SensorStateClass.MEASUREMENT,
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
            },
            "expected_state": str(float(sum(VALUES))),
            "expected_state_class": SensorStateClass.MEASUREMENT,
            # First sensor now has a device class
            "expected_device_class": SensorDeviceClass.HUMIDITY,
            "expected_unit_of_measurement": PERCENTAGE,
        },
        {
            "entity": entity_ids[0],
            "value": str(VALUES[0]),
            "attributes": {
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "expected_state": str(float(sum(VALUES))),
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_device_class": None,
            "expected_unit_of_measurement": None,
        },
    ]

    for test_case in test_cases:
        hass.states.async_set(
            test_case["entity"],
            test_case["value"],
            test_case["attributes"],
        )
        await hass.async_block_till_done()
        state = hass.states.get("sensor.test_sum")
        assert state.state == test_case["expected_state"]
        assert state.attributes.get("state_class") == test_case["expected_state_class"]
        assert (
            state.attributes.get("device_class") == test_case["expected_device_class"]
        )
        assert (
            state.attributes.get("unit_of_measurement")
            == test_case["expected_unit_of_measurement"]
        )