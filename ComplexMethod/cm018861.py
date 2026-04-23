async def test_rgb_or_w_light(hass: HomeAssistant) -> None:
    """Test an rgb or w light."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.color_modes = FLUX_COLOR_MODES_RGB_W
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
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["rgb", "white"]
    assert attributes[ATTR_RGB_COLOR] == (255, 0, 0)

    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    bulb.async_turn_off.assert_called_once()
    await async_mock_device_turn_off(hass, bulb)

    assert hass.states.get(entity_id).state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    bulb.async_turn_on.assert_called_once()
    bulb.async_turn_on.reset_mock()
    bulb.is_on = True

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    bulb.async_set_brightness.assert_called_with(100)
    bulb.async_set_brightness.reset_mock()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_RGB_COLOR: (255, 255, 255),
            ATTR_BRIGHTNESS: 128,
        },
        blocking=True,
    )
    bulb.async_set_levels.assert_called_with(255, 255, 255, brightness=128)
    bulb.async_set_levels.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "random"},
        blocking=True,
    )
    bulb.async_set_effect.assert_called_once()
    bulb.async_set_effect.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "purple_fade", ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    bulb.async_set_effect.assert_called_with("purple_fade", 50, 100)
    bulb.async_set_effect.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_WHITE: 128,
        },
        blocking=True,
    )
    bulb.async_set_levels.assert_called_with(w=128)
    bulb.async_set_levels.reset_mock()

    bulb.color_mode = FLUX_COLOR_MODE_DIM

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_BRIGHTNESS: 100,
        },
        blocking=True,
    )
    bulb.async_set_brightness.assert_called_with(100)
    bulb.async_set_brightness.reset_mock()