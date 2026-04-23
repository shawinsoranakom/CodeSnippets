async def test_switchbox_init(
    switchbox, hass: HomeAssistant, device_registry: dr.DeviceRegistry, config
) -> None:
    """Test switch default state."""

    feature_mock, entity_id = switchbox

    feature_mock.async_update = AsyncMock()
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-switchBox-1afe34e750b8-0.relay"

    state = hass.states.get(entity_id)
    assert state.name == "My switch box switchBox-0.relay"

    assert state.attributes[ATTR_DEVICE_CLASS] == SwitchDeviceClass.SWITCH

    assert state.state == STATE_OFF

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My switch box"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "switchBox"
    assert device.sw_version == "1.23"