async def test_rgbw_light_auto_on(hass: HomeAssistant) -> None:
    """Test an rgbw light that does not need the turn on command sent."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.requires_turn_on = False
    bulb.raw_state = bulb.raw_state._replace(model_num=0x33)  # RGB only model
    bulb.color_modes = {FLUX_COLOR_MODE_RGBW}
    bulb.color_mode = FLUX_COLOR_MODE_RGBW
    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "light.bulb_rgbcw_ddeeff"

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 128
    assert attributes[ATTR_COLOR_MODE] == ColorMode.RGBW
    assert attributes[ATTR_EFFECT_LIST] == bulb.effect_list
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.RGBW]
    assert attributes[ATTR_HS_COLOR] == (0.0, 83.529)

    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    bulb.async_turn_off.assert_called_once()

    await async_mock_device_turn_off(hass, bulb)
    assert hass.states.get(entity_id).state == STATE_OFF

    bulb.brightness = 0
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (10, 10, 30, 0)},
        blocking=True,
    )
    # If the bulb is off and we are using existing brightness
    # it has to be at least 1 or the bulb won't turn on
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_levels.assert_called_with(10, 10, 30, 0)
    bulb.async_set_levels.reset_mock()
    bulb.async_turn_on.reset_mock()

    # Should still be called with no kwargs
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    bulb.async_turn_on.assert_called_once()
    await async_mock_device_turn_on(hass, bulb)
    assert hass.states.get(entity_id).state == STATE_ON
    bulb.async_turn_on.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_brightness.assert_called_with(100)
    bulb.async_set_brightness.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (0, 0, 0, 0)},
        blocking=True,
    )
    # If the bulb is on and we are using existing brightness
    # and brightness was 0 we need to set it to at least 1
    # or the device may not turn on. In this case we scale
    # the current color to brightness of 1 to ensure the device
    # does not switch to white since otherwise we do not have
    # enough resolution to determine which color to display
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_brightness.assert_not_called()
    bulb.async_set_levels.assert_called_with(3, 0, 0, 0)
    bulb.async_set_levels.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (0, 0, 0, 56)},
        blocking=True,
    )
    # If the bulb is on and we are using existing brightness
    # and brightness was 0 we need to set it to at least 1
    # or the device may not turn on. In this case we scale
    # the current color to brightness of 1 to ensure the device
    # does not switch to white since otherwise we do not have
    # enough resolution to determine which color to display
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_brightness.assert_not_called()
    bulb.async_set_levels.assert_called_with(3, 0, 0, 56)
    bulb.async_set_levels.reset_mock()

    bulb.brightness = 128
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_levels.assert_called_with(110, 19, 0, 255)
    bulb.async_set_levels.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "random"},
        blocking=True,
    )
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_effect.assert_called_once()
    bulb.async_set_effect.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "purple_fade"},
        blocking=True,
    )
    bulb.async_turn_on.assert_not_called()
    bulb.async_set_effect.assert_called_with("purple_fade", 50, 50)
    bulb.async_set_effect.reset_mock()