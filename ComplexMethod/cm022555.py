async def test_init(
    tempsensor, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test sensor default state."""

    _, entity_id = tempsensor
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-tempSensor-1afe34db9437-0.temperature"

    state = hass.states.get(entity_id)
    assert state.name == "My temperature sensor tempSensor-0.temperature"

    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My temperature sensor"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "tempSensor"
    assert device.sw_version == "1.23"