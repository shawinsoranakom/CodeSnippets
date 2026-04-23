async def test_rgbcw_light(hass: HomeAssistant) -> None:
    """Test an rgbcw light."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.raw_state = bulb.raw_state._replace(warm_white=1, cool_white=2)
    bulb.color_modes = {FLUX_COLOR_MODE_RGBWW, FLUX_COLOR_MODE_CCT}
    bulb.color_mode = FLUX_COLOR_MODE_RGBWW
    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "light.bulb_rgbcw_ddeeff"

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_COLOR_MODE] == "rgbww"
    assert attributes[ATTR_EFFECT_LIST] == bulb.effect_list
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp", "rgbww"]
    assert attributes[ATTR_HS_COLOR] == (3.237, 94.51)

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

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    bulb.async_set_brightness.assert_called_with(100)
    bulb.async_set_brightness.reset_mock()
    bulb.is_on = True

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_RGBWW_COLOR: (255, 255, 255, 0, 255),
            ATTR_BRIGHTNESS: 128,
        },
        blocking=True,
    )
    bulb.async_set_levels.assert_called_with(192, 192, 192, 192, 0)
    bulb.async_set_levels.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBWW_COLOR: (255, 255, 255, 255, 50)},
        blocking=True,
    )
    bulb.async_set_levels.assert_called_with(255, 255, 255, 50, 255)
    bulb.async_set_levels.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 6493},
        blocking=True,
    )
    bulb.async_set_white_temp.assert_called_with(6493, 255)
    bulb.async_set_white_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 6493, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    bulb.async_set_white_temp.assert_called_with(6493, 255)
    bulb.async_set_white_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 3448},
        blocking=True,
    )
    bulb.async_set_white_temp.assert_called_with(3448, 255)
    bulb.async_set_white_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBWW_COLOR: (255, 191, 178, 0, 0)},
        blocking=True,
    )
    bulb.async_set_levels.assert_called_with(255, 191, 178, 0, 0)
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
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "purple_fade"},
        blocking=True,
    )
    bulb.async_set_effect.assert_called_with("purple_fade", 50, 50)
    bulb.async_set_effect.reset_mock()
    bulb.effect = "purple_fade"
    bulb.brightness = 128

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    bulb.async_set_brightness.assert_called_with(255)
    bulb.async_set_brightness.reset_mock()

    await async_mock_device_turn_off(hass, bulb)
    bulb.color_mode = FLUX_COLOR_MODE_RGBWW
    bulb.brightness = MIN_RGB_BRIGHTNESS
    bulb.rgb = (MIN_RGB_BRIGHTNESS, MIN_RGB_BRIGHTNESS, MIN_RGB_BRIGHTNESS)
    await async_mock_device_turn_on(hass, bulb)
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.RGBWW
    assert state.attributes[ATTR_BRIGHTNESS] == 1

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 5882},
        blocking=True,
    )
    bulb.async_set_white_temp.assert_called_with(5882, MIN_CCT_BRIGHTNESS)
    bulb.async_set_white_temp.reset_mock()