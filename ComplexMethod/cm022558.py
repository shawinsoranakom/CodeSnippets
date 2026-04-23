async def test_wlightbox_s_init(
    wlightbox_s, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test cover default state."""

    _, entity_id = wlightbox_s
    entry = await async_setup_entity(hass, entity_id)
    assert entry.unique_id == "BleBox-wLightBoxS-1afe34e750b8-color"

    state = hass.states.get(entity_id)
    assert state.name == "My wLightBoxS wLightBoxS-color"

    color_modes = state.attributes[ATTR_SUPPORTED_COLOR_MODES]
    assert color_modes == [ColorMode.BRIGHTNESS]

    assert state.attributes[ATTR_BRIGHTNESS] is None
    assert state.state == STATE_UNKNOWN

    device = device_registry.async_get(entry.device_id)

    assert device.name == "My wLightBoxS"
    assert device.identifiers == {("blebox", "abcd0123ef5678")}
    assert device.manufacturer == "BleBox"
    assert device.model == "wLightBoxS"
    assert device.sw_version == "1.23"