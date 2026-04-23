async def test_dimmer_init(
    dimmer, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test cover default state."""

    _, entity_id = dimmer
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-dimmerBox-1afe34e750b8-brightness"

    state = hass.states.get(entity_id)
    assert state.name == "My dimmer dimmerBox-brightness"

    color_modes = state.attributes[ATTR_SUPPORTED_COLOR_MODES]
    assert color_modes == [ColorMode.BRIGHTNESS]

    assert state.attributes[ATTR_BRIGHTNESS] == 65
    assert state.state == STATE_ON

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My dimmer"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "dimmerBox"
    assert device.sw_version == "1.23"