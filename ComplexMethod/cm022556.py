async def test_airsensor_init(
    airsensor, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test airSensor default state."""

    _, entity_id = airsensor
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-airSensor-1afe34db9437-0.air"

    state = hass.states.get(entity_id)
    assert state.name == "My air sensor airSensor-0.air"

    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.PM1
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My air sensor"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "airSensor"
    assert device.sw_version == "1.23"