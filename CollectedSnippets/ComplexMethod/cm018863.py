async def test_rgb_light_custom_effects(hass: HomeAssistant) -> None:
    """Test an rgb light with a custom effect."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
        options={
            CONF_MODE: "auto",
            CONF_CUSTOM_EFFECT_COLORS: "[0,0,255], [255,0,0]",
            CONF_CUSTOM_EFFECT_SPEED_PCT: 88,
            CONF_CUSTOM_EFFECT_TRANSITION: TRANSITION_JUMP,
        },
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
    assert attributes[ATTR_EFFECT_LIST] == [*bulb.effect_list, "custom"]
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["rgb"]
    assert attributes[ATTR_HS_COLOR] == (0, 100)

    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    bulb.async_turn_off.assert_called_once()
    await async_mock_device_turn_off(hass, bulb)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "custom"},
        blocking=True,
    )
    bulb.effect = "custom"
    bulb.async_set_custom_pattern.assert_called_with(
        [[0, 0, 255], [255, 0, 0]], 88, "jump"
    )
    bulb.async_set_custom_pattern.reset_mock()
    await async_mock_device_turn_on(hass, bulb)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_EFFECT] == "custom"

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 55, ATTR_EFFECT: "custom"},
        blocking=True,
    )
    bulb.effect = "custom"
    bulb.async_set_custom_pattern.assert_called_with(
        [[0, 0, 255], [255, 0, 0]], 88, "jump"
    )
    bulb.async_set_custom_pattern.reset_mock()
    await async_mock_device_turn_on(hass, bulb)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_EFFECT] == "custom"