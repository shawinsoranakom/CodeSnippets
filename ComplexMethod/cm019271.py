async def test_sensor_calculated_result_fails_on_uom(hass: HomeAssistant) -> None:
    """Test the sensor calculating fails as UoM not part of device class."""
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
            "device_class": SensorDeviceClass.ENERGY,
            "state_class": SensorStateClass.TOTAL,
            "unit_of_measurement": "kWh",
        },
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == str(float(sum(VALUES)))
    assert state.attributes.get("device_class") == "energy"
    assert state.attributes.get("state_class") == "total"
    assert state.attributes.get("unit_of_measurement") == "kWh"

    hass.states.async_set(
        entity_ids[2],
        "12",
        {
            "device_class": SensorDeviceClass.ENERGY,
            "state_class": SensorStateClass.TOTAL,
        },
        True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sum")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("device_class") == "energy"
    assert state.attributes.get("state_class") == "total"
    assert state.attributes.get("unit_of_measurement") is None