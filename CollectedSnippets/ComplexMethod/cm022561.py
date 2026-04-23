async def test_switchbox_d_init(
    switchbox_d, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test switch default state."""

    feature_mocks, entity_ids = switchbox_d

    feature_mocks[0].async_update = AsyncMock()
    feature_mocks[1].async_update = AsyncMock()
    entries = await async_setup_entities(hass, entity_ids)

    entry = entries[0]
    assert entry.unique_id == "BleBox-switchBoxD-1afe34e750b8-0.relay"

    state = hass.states.get(entity_ids[0])
    assert state.name == "My relays switchBoxD-0.relay"
    assert state.attributes[ATTR_DEVICE_CLASS] == SwitchDeviceClass.SWITCH
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My relays"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "switchBoxD"
    assert device.sw_version == "1.23"

    entry = entries[1]
    assert entry.unique_id == "BleBox-switchBoxD-1afe34e750b8-1.relay"

    state = hass.states.get(entity_ids[1])
    assert state.name == "My relays switchBoxD-1.relay"
    assert state.attributes[ATTR_DEVICE_CLASS] == SwitchDeviceClass.SWITCH
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My relays"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "switchBoxD"
    assert device.sw_version == "1.23"