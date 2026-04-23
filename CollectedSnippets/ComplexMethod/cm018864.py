async def test_rgb_light_custom_effects_invalid_colors(
    hass: HomeAssistant, effect_colors: str
) -> None:
    """Test an rgb light with a invalid effect."""
    options = {
        CONF_MODE: "auto",
        CONF_CUSTOM_EFFECT_SPEED_PCT: 88,
        CONF_CUSTOM_EFFECT_TRANSITION: TRANSITION_JUMP,
    }
    if effect_colors:
        options[CONF_CUSTOM_EFFECT_COLORS] = effect_colors
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        options=options,
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.color_modes = {FLUX_COLOR_MODE_RGB}
    bulb.color_mode = FLUX_COLOR_MODE_RGB
    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "light.bulb_rgbcw_ddeeff"

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_COLOR_MODE] == "rgb"
    assert attributes[ATTR_EFFECT_LIST] == bulb.effect_list
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["rgb"]
    assert attributes[ATTR_HS_COLOR] == (0, 100)