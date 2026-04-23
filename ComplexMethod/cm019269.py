async def test_sensor_with_uoms_but_no_device_class(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the sensor works with same uom when there is no device class."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": "test_sum",
            "type": "sum",
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id_last_sensor",
        }
    }

    entity_ids = config["sensor"]["entities"]

    hass.states.async_set(
        entity_ids[0],
        str(VALUES[0]),
        {
            "device_class": SensorDeviceClass.POWER,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "W",
        },
    )
    hass.states.async_set(
        entity_ids[1],
        str(VALUES[1]),
        {
            "device_class": SensorDeviceClass.POWER,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "W",
        },
    )
    hass.states.async_set(
        entity_ids[2],
        str(VALUES[2]),
        {
            "unit_of_measurement": "W",
        },
    )

    await hass.async_block_till_done()

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("state_class") is None
    assert state.attributes.get("unit_of_measurement") == "W"
    assert state.state == str(float(sum(VALUES)))

    assert not [
        issue for issue in issue_registry.issues.values() if issue.domain == DOMAIN
    ]

    hass.states.async_set(
        entity_ids[0],
        str(VALUES[0]),
        {
            "device_class": SensorDeviceClass.POWER,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "kW",
        },
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_sum")
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("state_class") is None
    assert state.attributes.get("unit_of_measurement") is None
    assert state.state == STATE_UNKNOWN

    assert (
        "Unable to use state. Only entities with correct unit of measurement is supported"
        in caplog.text
    )

    hass.states.async_set(
        entity_ids[0],
        str(VALUES[0]),
        {
            "device_class": SensorDeviceClass.POWER,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "W",
        },
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_sum")
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("state_class") is None
    assert state.attributes.get("unit_of_measurement") == "W"
    assert state.state == str(float(sum(VALUES)))