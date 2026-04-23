async def test_state(hass: HomeAssistant, method) -> None:
    """Test integration sensor state."""
    config = {
        "sensor": {
            "platform": "integration",
            "name": "integration",
            "source": "sensor.power",
            "round": 2,
            "method": method,
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state is not None
    assert state.attributes.get("state_class") is SensorStateClass.TOTAL
    assert "device_class" not in state.attributes

    now = dt_util.utcnow()
    with freeze_time(now):
        entity_id = config["sensor"]["source"]
        hass.states.async_set(
            entity_id,
            1,
            {
                ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT,
            },
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state is not None
    assert state.attributes.get("state_class") is SensorStateClass.TOTAL
    assert "device_class" not in state.attributes

    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            1,
            {
                "device_class": SensorDeviceClass.POWER,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT,
            },
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state is not None

    # Testing a power sensor at 1 KiloWatts for 1hour = 1kWh
    assert round(float(state.state), config["sensor"]["round"]) == 1.0

    assert state.attributes.get("unit_of_measurement") == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get("device_class") == SensorDeviceClass.ENERGY
    assert state.attributes.get("state_class") is SensorStateClass.TOTAL

    # 1 hour after last update, power sensor is unavailable
    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            STATE_UNAVAILABLE,
            {
                "device_class": SensorDeviceClass.POWER,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT,
            },
            force_update=True,
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.integration")
    assert state.state == STATE_UNAVAILABLE

    # 1 hour after last update, power sensor is back to normal at 2 KiloWatts and stays for 1 hour += 2kWh
    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            2,
            {
                "device_class": SensorDeviceClass.POWER,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT,
            },
            force_update=True,
        )
        await hass.async_block_till_done()
    state = hass.states.get("sensor.integration")
    assert (
        round(float(state.state), config["sensor"]["round"]) == 3.0
        if method == "right"
        else 1.0
    )

    now += timedelta(seconds=3600)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            2,
            {
                "device_class": SensorDeviceClass.POWER,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfPower.KILO_WATT,
            },
            force_update=True,
        )
        await hass.async_block_till_done()
    state = hass.states.get("sensor.integration")
    assert (
        round(float(state.state), config["sensor"]["round"]) == 5.0
        if method == "right"
        else 3.0
    )