async def test_sensor_calculated_properties_not_same(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """Test the sensor calculating device_class, state_class and unit of measurement not same."""
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
            "device_class": SensorDeviceClass.ENERGY,
            "state_class": SensorStateClass.TOTAL,
            "unit_of_measurement": "kWh",
        },
    )
    hass.states.async_set(
        entity_ids[1],
        str(VALUES[1]),
        {
            "device_class": SensorDeviceClass.ENERGY,
            "state_class": SensorStateClass.TOTAL,
            "unit_of_measurement": "kWh",
        },
    )
    hass.states.async_set(
        entity_ids[2],
        str(VALUES[2]),
        {
            "device_class": SensorDeviceClass.CURRENT,
            "state_class": SensorStateClass.MEASUREMENT,
            "unit_of_measurement": "A",
        },
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == str(float(sum(VALUES)))
    assert state.attributes.get("device_class") is None
    assert state.attributes.get("state_class") is None
    assert state.attributes.get("unit_of_measurement") is None

    assert issue_registry.async_get_issue(
        DOMAIN, "sensor.test_sum_uoms_not_matching_no_device_class"
    )
    assert issue_registry.async_get_issue(
        DOMAIN, "sensor.test_sum_device_classes_not_matching"
    )
    assert issue_registry.async_get_issue(
        DOMAIN, "sensor.test_sum_state_classes_not_matching"
    )