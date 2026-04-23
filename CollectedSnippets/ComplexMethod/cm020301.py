async def test_thermostat_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    create_device: CreateDevice,
    setup_platform: PlatformSetup,
) -> None:
    """Test a thermostat with temperature and humidity sensors."""
    create_device.create(
        {
            "sdm.devices.traits.Temperature": {
                "ambientTemperatureCelsius": 25.1,
            },
            "sdm.devices.traits.Humidity": {
                "ambientHumidityPercent": 35.0,
            },
        }
    )
    await setup_platform()

    temperature = hass.states.get("sensor.my_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "25.1"
    assert (
        temperature.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == UnitOfTemperature.CELSIUS
    )
    assert (
        temperature.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TEMPERATURE
    )
    assert temperature.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert temperature.attributes.get(ATTR_FRIENDLY_NAME) == "My Sensor Temperature"

    humidity = hass.states.get("sensor.my_sensor_humidity")
    assert humidity is not None
    assert humidity.state == "35"
    assert humidity.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE
    assert humidity.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.HUMIDITY
    assert humidity.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert humidity.attributes.get(ATTR_FRIENDLY_NAME) == "My Sensor Humidity"

    entry = entity_registry.async_get("sensor.my_sensor_temperature")
    assert entry.unique_id == f"{DEVICE_ID}-temperature"
    assert entry.domain == "sensor"

    entry = entity_registry.async_get("sensor.my_sensor_humidity")
    assert entry.unique_id == f"{DEVICE_ID}-humidity"
    assert entry.domain == "sensor"

    device = device_registry.async_get(entry.device_id)
    assert device.name == "My Sensor"
    assert device.model == "Thermostat"
    assert device.identifiers == {("nest", DEVICE_ID)}