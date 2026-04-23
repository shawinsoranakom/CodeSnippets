async def test_laundrify_sensor_init(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_device: LaundrifyDevice,
    laundrify_config_entry: MockConfigEntry,
) -> None:
    """Test Laundrify sensor default state."""
    device_slug = slugify(mock_device.name, separator="_")

    state = hass.states.get(f"sensor.{device_slug}_power")
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.POWER
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get_device({(DOMAIN, mock_device.id)})
    assert device is not None
    assert device.name == mock_device.name
    assert device.identifiers == {(DOMAIN, mock_device.id)}
    assert device.manufacturer == mock_device.manufacturer
    assert device.model == MODELS[mock_device.model]
    assert device.sw_version == mock_device.firmwareVersion