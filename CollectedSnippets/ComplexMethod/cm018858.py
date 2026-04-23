async def test_rgb_cct_light(hass: HomeAssistant) -> None:
    """Test an rgb cct light."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.raw_state = bulb.raw_state._replace(model_num=0x35)  # RGB & CCT model
    bulb.color_modes = {FLUX_COLOR_MODE_RGB, FLUX_COLOR_MODE_CCT}
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
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp", "rgb"]
    assert attributes[ATTR_HS_COLOR] == (0, 100)

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

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    bulb.async_set_levels.assert_called_with(255, 191, 178, brightness=128)
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
    bulb.color_mode = FLUX_COLOR_MODE_CCT
    bulb.getWhiteTemperature = Mock(return_value=(5000, 128))
    bulb.color_temp = 5000

    bulb.raw_state = bulb.raw_state._replace(
        red=0, green=0, blue=0, warm_white=1, cool_white=2
    )
    await async_mock_device_turn_on(hass, bulb)
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_COLOR_MODE] == "color_temp"
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp", "rgb"]
    assert attributes[ATTR_COLOR_TEMP_KELVIN] == 5000

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 2702},
        blocking=True,
    )
    bulb.async_set_white_temp.assert_called_with(2702, 128)
    bulb.async_set_white_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    bulb.async_set_brightness.assert_called_with(255)
    bulb.async_set_brightness.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    bulb.async_set_brightness.assert_called_with(128)
    bulb.async_set_brightness.reset_mock()