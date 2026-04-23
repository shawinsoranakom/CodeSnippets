async def test_init_gatecontroller(
    gatecontroller, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test gateController default state."""

    _, entity_id = gatecontroller
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-gateController-2bee34e750b8-position"

    state = hass.states.get(entity_id)
    assert state.name == "My gate controller gateController-position"
    assert state.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.GATE

    supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
    assert supported_features & CoverEntityFeature.OPEN
    assert supported_features & CoverEntityFeature.CLOSE
    assert supported_features & CoverEntityFeature.STOP

    assert supported_features & CoverEntityFeature.SET_POSITION
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My gate controller"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "gateController"
    assert device.sw_version == "1.23"