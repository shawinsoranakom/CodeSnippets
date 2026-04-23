async def test_wlightbox_init(
    wlightbox, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test cover default state."""

    _, entity_id = wlightbox
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-wLightBox-1afe34e750b8-color"

    state = hass.states.get(entity_id)
    assert state.name == "My wLightBox wLightBox-color"

    color_modes = state.attributes[ATTR_SUPPORTED_COLOR_MODES]
    assert color_modes == [ColorMode.RGBW]

    assert state.attributes[ATTR_BRIGHTNESS] is None
    assert state.attributes[ATTR_RGBW_COLOR] is None
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My wLightBox"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "wLightBox"
    assert device.sw_version == "1.23"