async def test_init_shutterbox(
    shutterbox, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test gateBox default state."""

    _, entity_id = shutterbox
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-shutterBox-2bee34e750b8-position"

    state = hass.states.get(entity_id)
    assert state.name == "My shutter shutterBox-position"
    assert entry.original_device_class == CoverDeviceClass.SHUTTER

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    assert supported_features & CoverEntityFeature.OPEN
    assert supported_features & CoverEntityFeature.CLOSE
    assert supported_features & CoverEntityFeature.STOP

    assert supported_features & CoverEntityFeature.SET_POSITION
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My shutter"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "shutterBox"
    assert device.sw_version == "1.23"