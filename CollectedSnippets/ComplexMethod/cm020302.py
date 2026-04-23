async def test_device_with_unknown_type(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    create_device: CreateDevice,
    setup_platform: PlatformSetup,
) -> None:
    """Test a device without a custom name, inferring name from structure."""
    create_device.create(
        {
            "sdm.devices.traits.Temperature": {
                "ambientTemperatureCelsius": 25.1,
            },
        }
    )
    await setup_platform()

    temperature = hass.states.get("sensor.my_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "25.1"
    assert temperature.attributes.get(ATTR_FRIENDLY_NAME) == "My Sensor Temperature"

    entry = entity_registry.async_get("sensor.my_sensor_temperature")
    assert entry.unique_id == f"{DEVICE_ID}-temperature"
    assert entry.domain == "sensor"

    device = device_registry.async_get(entry.device_id)
    assert device.name == "My Sensor"
    assert device.model is None
    assert device.identifiers == {("nest", DEVICE_ID)}