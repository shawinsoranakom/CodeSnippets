async def test_rgb_light(hass: HomeAssistant) -> None:
    """Test an rgb light."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.raw_state = bulb.raw_state._replace(model_num=0x33)  # RGB only model
    bulb.color_modes = {FLUX_COLOR_MODE_RGB}
    bulb.color_mode = FLUX_COLOR_MODE_RGB
    with _patch_discovery(no_device=True), _patch_wifibulb(device=bulb):
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
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: (10, 10, 30)},
        blocking=True,
    )
    # If the bulb is off and we are using existing brightness
    # it has to be at least 1 or the bulb won't turn on
    bulb.async_set_levels.assert_called_with(10, 10, 30, brightness=1)
    bulb.async_set_levels.reset_mock()
    bulb.async_turn_on.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    # If its off and the device requires the turn on
    # command before setting brightness we need to make sure its called
    bulb.async_turn_on.assert_called_once()
    bulb.async_set_brightness.assert_called_with(100)
    bulb.async_set_brightness.reset_mock()
    await async_mock_device_turn_on(hass, bulb)
    assert hass.states.get(entity_id).state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: (10, 10, 30)},
        blocking=True,
    )
    # If the bulb is on and we are using existing brightness
    # and brightness was 0 older devices will not be able to turn on
    # so we need to make sure its at least 1 and that we
    # call it before the turn on command since the device
    # does not support auto on
    bulb.async_set_levels.assert_called_with(10, 10, 30, brightness=1)
    bulb.async_set_levels.reset_mock()

    bulb.brightness = 128
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