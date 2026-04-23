async def test_services(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Test Yeelight services."""
    assert await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **CONFIG_ENTRY_DATA,
            CONF_MODE_MUSIC: True,
            CONF_SAVE_ON_CHANGE: True,
            CONF_NIGHTLIGHT_SWITCH: True,
        },
    )
    config_entry.add_to_hass(hass)

    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get(ENTITY_LIGHT).state == STATE_ON
    assert hass.states.get(ENTITY_NIGHTLIGHT).state == STATE_OFF

    async def _async_test_service(
        service,
        data,
        method,
        payload=None,
        domain=DOMAIN,
        failure_side_effect=HomeAssistantError,
    ):
        err_count = len([x for x in caplog.records if x.levelno == logging.ERROR])

        # success
        if method.startswith("async_"):
            mocked_method = AsyncMock()
        else:
            mocked_method = MagicMock()
        setattr(mocked_bulb, method, mocked_method)
        await hass.services.async_call(domain, service, data, blocking=True)
        if payload is None:
            mocked_method.assert_called_once()
        elif isinstance(payload, list):
            mocked_method.assert_called_once_with(*payload)
        else:
            mocked_method.assert_called_once_with(**payload)
        assert (
            len([x for x in caplog.records if x.levelno == logging.ERROR]) == err_count
        )

        # failure
        if failure_side_effect:
            if method.startswith("async_"):
                mocked_method = AsyncMock(side_effect=failure_side_effect)
            else:
                mocked_method = MagicMock(side_effect=failure_side_effect)
            setattr(mocked_bulb, method, mocked_method)
            with pytest.raises(failure_side_effect):
                await hass.services.async_call(domain, service, data, blocking=True)

    # turn_on rgb_color
    brightness = 100
    rgb_color = (0, 128, 255)
    transition = 2
    mocked_bulb.last_properties["power"] = "off"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS: brightness,
            ATTR_RGB_COLOR: rgb_color,
            ATTR_FLASH: FLASH_LONG,
            ATTR_EFFECT: EFFECT_STOP,
            ATTR_TRANSITION: transition,
        },
        blocking=True,
    )
    mocked_bulb.async_turn_on.assert_called_once_with(
        duration=transition * 1000,
        light_type=LightType.Main,
        power_mode=PowerMode.NORMAL,
    )
    mocked_bulb.async_turn_on.reset_mock()
    mocked_bulb.async_start_music.assert_called_once()
    mocked_bulb.async_start_music.reset_mock()
    mocked_bulb.async_set_brightness.assert_called_once_with(
        brightness / 255 * 100, duration=transition * 1000, light_type=LightType.Main
    )
    mocked_bulb.async_set_brightness.reset_mock()
    mocked_bulb.async_set_color_temp.assert_not_called()
    mocked_bulb.async_set_color_temp.reset_mock()
    mocked_bulb.async_set_hsv.assert_not_called()
    mocked_bulb.async_set_hsv.reset_mock()
    mocked_bulb.async_set_rgb.assert_called_once_with(
        *rgb_color, duration=transition * 1000, light_type=LightType.Main
    )
    mocked_bulb.async_set_rgb.reset_mock()
    mocked_bulb.async_start_flow.assert_called_once()  # flash
    mocked_bulb.async_start_flow.reset_mock()
    mocked_bulb.async_stop_flow.assert_called_once_with(light_type=LightType.Main)
    mocked_bulb.async_stop_flow.reset_mock()

    # turn_on hs_color
    brightness = 100
    hs_color = (180, 100)
    transition = 2
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS: brightness,
            ATTR_HS_COLOR: hs_color,
            ATTR_FLASH: FLASH_LONG,
            ATTR_EFFECT: EFFECT_STOP,
            ATTR_TRANSITION: transition,
        },
        blocking=True,
    )
    mocked_bulb.async_turn_on.assert_called_once_with(
        duration=transition * 1000,
        light_type=LightType.Main,
        power_mode=PowerMode.NORMAL,
    )
    mocked_bulb.async_turn_on.reset_mock()
    mocked_bulb.async_start_music.assert_called_once()
    mocked_bulb.async_start_music.reset_mock()
    mocked_bulb.async_set_brightness.assert_called_once_with(
        brightness / 255 * 100, duration=transition * 1000, light_type=LightType.Main
    )
    mocked_bulb.async_set_brightness.reset_mock()
    mocked_bulb.async_set_color_temp.assert_not_called()
    mocked_bulb.async_set_color_temp.reset_mock()
    mocked_bulb.async_set_hsv.assert_called_once_with(
        *hs_color, duration=transition * 1000, light_type=LightType.Main
    )
    mocked_bulb.async_set_hsv.reset_mock()
    mocked_bulb.async_set_rgb.assert_not_called()
    mocked_bulb.async_set_rgb.reset_mock()
    mocked_bulb.async_start_flow.assert_called_once()  # flash
    mocked_bulb.async_start_flow.reset_mock()
    mocked_bulb.async_stop_flow.assert_called_once_with(light_type=LightType.Main)
    mocked_bulb.async_stop_flow.reset_mock()

    # turn_on color_temp
    brightness = 100
    color_temp = 5000
    transition = 1
    mocked_bulb.last_properties["power"] = "off"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS: brightness,
            ATTR_COLOR_TEMP_KELVIN: color_temp,
            ATTR_FLASH: FLASH_LONG,
            ATTR_EFFECT: EFFECT_STOP,
            ATTR_TRANSITION: transition,
        },
        blocking=True,
    )
    mocked_bulb.async_turn_on.assert_called_once_with(
        duration=transition * 1000,
        light_type=LightType.Main,
        power_mode=PowerMode.NORMAL,
    )
    mocked_bulb.async_turn_on.reset_mock()
    mocked_bulb.async_start_music.assert_called_once()
    mocked_bulb.async_set_brightness.assert_called_once_with(
        brightness / 255 * 100, duration=transition * 1000, light_type=LightType.Main
    )
    mocked_bulb.async_set_color_temp.assert_called_once_with(
        color_temp,
        duration=transition * 1000,
        light_type=LightType.Main,
    )
    mocked_bulb.async_set_hsv.assert_not_called()
    mocked_bulb.async_set_rgb.assert_not_called()
    mocked_bulb.async_start_flow.assert_called_once()  # flash
    mocked_bulb.async_stop_flow.assert_called_once_with(light_type=LightType.Main)

    # turn_on color_temp - flash short
    brightness = 100
    color_temp = 5000
    transition = 1
    mocked_bulb.async_start_music.reset_mock()
    mocked_bulb.async_set_brightness.reset_mock()
    mocked_bulb.async_set_color_temp.reset_mock()
    mocked_bulb.async_start_flow.reset_mock()
    mocked_bulb.async_stop_flow.reset_mock()

    mocked_bulb.last_properties["power"] = "off"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS: brightness,
            ATTR_COLOR_TEMP_KELVIN: color_temp,
            ATTR_FLASH: FLASH_SHORT,
            ATTR_EFFECT: EFFECT_STOP,
            ATTR_TRANSITION: transition,
        },
        blocking=True,
    )
    mocked_bulb.async_turn_on.assert_called_once_with(
        duration=transition * 1000,
        light_type=LightType.Main,
        power_mode=PowerMode.NORMAL,
    )
    mocked_bulb.async_turn_on.reset_mock()
    mocked_bulb.async_start_music.assert_called_once()
    mocked_bulb.async_set_brightness.assert_called_once_with(
        brightness / 255 * 100, duration=transition * 1000, light_type=LightType.Main
    )
    mocked_bulb.async_set_color_temp.assert_called_once_with(
        color_temp,
        duration=transition * 1000,
        light_type=LightType.Main,
    )
    mocked_bulb.async_set_hsv.assert_not_called()
    mocked_bulb.async_set_rgb.assert_not_called()
    mocked_bulb.async_start_flow.assert_called_once()  # flash
    mocked_bulb.async_stop_flow.assert_called_once_with(light_type=LightType.Main)

    # turn_on nightlight
    await _async_test_service(
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_NIGHTLIGHT},
        "async_turn_on",
        payload={
            "duration": DEFAULT_TRANSITION,
            "light_type": LightType.Main,
            "power_mode": PowerMode.MOONLIGHT,
        },
        domain="light",
    )

    mocked_bulb.last_properties["power"] = "on"
    assert hass.states.get(ENTITY_LIGHT).state != STATE_UNAVAILABLE
    # turn_off
    await _async_test_service(
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_TRANSITION: transition},
        "async_turn_off",
        domain="light",
        payload={"duration": transition * 1000, "light_type": LightType.Main},
    )

    # set_mode
    mode = "rgb"
    await _async_test_service(
        SERVICE_SET_MODE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_MODE: "rgb"},
        "async_set_power_mode",
        [PowerMode[mode.upper()]],
    )

    # start_flow
    await _async_test_service(
        SERVICE_START_FLOW,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_TRANSITIONS: [{YEELIGHT_TEMPERATURE_TRANSACTION: [1900, 2000, 60]}],
        },
        "async_start_flow",
    )

    # set_color_scene
    await _async_test_service(
        SERVICE_SET_COLOR_SCENE,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_RGB_COLOR: [10, 20, 30],
            ATTR_BRIGHTNESS: 50,
        },
        "async_set_scene",
        [SceneClass.COLOR, 10, 20, 30, 50],
    )

    # set_hsv_scene
    await _async_test_service(
        SERVICE_SET_HSV_SCENE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_HS_COLOR: [180, 50], ATTR_BRIGHTNESS: 50},
        "async_set_scene",
        [SceneClass.HSV, 180, 50, 50],
    )

    # set_color_temp_scene
    await _async_test_service(
        SERVICE_SET_COLOR_TEMP_SCENE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_KELVIN: 4000, ATTR_BRIGHTNESS: 50},
        "async_set_scene",
        [SceneClass.CT, 4000, 50],
    )

    # set_color_flow_scene
    await _async_test_service(
        SERVICE_SET_COLOR_FLOW_SCENE,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_TRANSITIONS: [{YEELIGHT_TEMPERATURE_TRANSACTION: [1900, 2000, 60]}],
        },
        "async_set_scene",
    )

    # set_auto_delay_off_scene
    await _async_test_service(
        SERVICE_SET_AUTO_DELAY_OFF_SCENE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_MINUTES: 1, ATTR_BRIGHTNESS: 50},
        "async_set_scene",
        [SceneClass.AUTO_DELAY_OFF, 50, 1],
    )

    # set_music_mode failure enable
    mocked_bulb.async_start_music = MagicMock(side_effect=AssertionError)
    assert "Unable to turn on music mode, consider disabling it" not in caplog.text
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_MUSIC_MODE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_MODE_MUSIC: "true"},
        blocking=True,
    )
    assert mocked_bulb.async_start_music.mock_calls == [call()]
    assert "Unable to turn on music mode, consider disabling it" in caplog.text

    # set_music_mode disable
    await _async_test_service(
        SERVICE_SET_MUSIC_MODE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_MODE_MUSIC: "false"},
        "async_stop_music",
        failure_side_effect=None,
    )

    # set_music_mode success enable
    await _async_test_service(
        SERVICE_SET_MUSIC_MODE,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_MODE_MUSIC: "true"},
        "async_start_music",
        failure_side_effect=None,
    )
    # test _cmd wrapper error handler
    mocked_bulb.last_properties["power"] = "off"
    mocked_bulb.available = True
    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: ENTITY_LIGHT},
        blocking=True,
    )
    assert hass.states.get(ENTITY_LIGHT).state == STATE_OFF

    mocked_bulb.async_turn_on = AsyncMock()
    mocked_bulb.async_set_brightness = AsyncMock(side_effect=BulbException)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "light",
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_BRIGHTNESS: 50},
            blocking=True,
        )
    assert hass.states.get(ENTITY_LIGHT).state == STATE_OFF

    mocked_bulb.async_set_brightness = AsyncMock(side_effect=TimeoutError)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "light",
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_BRIGHTNESS: 55},
            blocking=True,
        )
    assert hass.states.get(ENTITY_LIGHT).state == STATE_OFF

    mocked_bulb.async_set_brightness = AsyncMock(side_effect=socket.error)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "light",
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_BRIGHTNESS: 55},
            blocking=True,
        )
    assert hass.states.get(ENTITY_LIGHT).state == STATE_UNAVAILABLE