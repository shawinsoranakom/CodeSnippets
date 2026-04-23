async def test_sensor_readings(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test for successfully setting up the Efergy platform."""
    await setup_platform(hass, aioclient_mock, SENSOR_DOMAIN)

    state = hass.states.get("sensor.efergy_power_usage")
    assert state.state == "1580"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    state = hass.states.get("sensor.efergy_energy_budget")
    assert state.state == "ok"
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    state = hass.states.get("sensor.efergy_daily_consumption")
    assert state.state == "38.21"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_weekly_consumption")
    assert state.state == "267.47"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_monthly_consumption")
    assert state.state == "1069.88"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_yearly_consumption")
    assert state.state == "13373.50"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_daily_energy_cost")
    assert state.state == "5.27"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.MONETARY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "EUR"
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_weekly_energy_cost")
    assert state.state == "36.89"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.MONETARY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "EUR"
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_monthly_energy_cost")
    assert state.state == "147.56"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.MONETARY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "EUR"
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_yearly_energy_cost")
    assert state.state == "1844.50"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.MONETARY
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "EUR"
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.TOTAL_INCREASING
    state = hass.states.get("sensor.efergy_power_usage_728386")
    assert state.state == "1628"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT