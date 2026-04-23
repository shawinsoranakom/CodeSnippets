async def test_init_gatebox(
    gatebox, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test cover default state."""

    _, entity_id = gatebox
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-gateBox-1afe34db9437-position"

    state = hass.states.get(entity_id)
    assert state.name == "My gatebox gateBox-position"
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.DOOR

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    assert supported_features & CoverEntityFeature.OPEN
    assert supported_features & CoverEntityFeature.CLOSE

    # Not available during init since requires fetching state to detect
    assert not supported_features & CoverEntityFeature.STOP

    assert not supported_features & CoverEntityFeature.SET_POSITION
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My gatebox"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "gateBox"
    assert device.sw_version == "1.23"