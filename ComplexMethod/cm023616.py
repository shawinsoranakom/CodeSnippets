async def test_transition(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test transition commands."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 2
    config["lt_st"] = 5  # 5 channel light (RGBCW)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_OFF
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mqtt_mock.async_publish.reset_mock()

    # Dim the light from 0->100: Speed should be 4*2=8
    await common.async_turn_on(hass, "light.tasmota_test", brightness=255, transition=4)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 8;NoDelay;Dimmer 100",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Dim the light from 0->100: Speed should be capped at 40
    await common.async_turn_on(
        hass, "light.tasmota_test", brightness=255, transition=100
    )
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 40;NoDelay;Dimmer 100",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Dim the light from 0->0: Speed should be 1
    await common.async_turn_on(hass, "light.tasmota_test", brightness=0, transition=100)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 1;NoDelay;Power1 OFF",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Dim the light from 0->50: Speed should be 4*2*2=16
    await common.async_turn_on(hass, "light.tasmota_test", brightness=128, transition=4)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 16;NoDelay;Dimmer 50",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Fake state update from the light
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":50}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128

    # Dim the light from 50->0: Speed should be 6*2*2=24
    await common.async_turn_off(hass, "light.tasmota_test", transition=6)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 24;NoDelay;Power1 OFF",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Fake state update from the light
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":100}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255

    # Dim the light from 100->0: Speed should be 0
    await common.async_turn_off(hass, "light.tasmota_test", transition=0)
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 0;NoDelay;Power1 OFF",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Fake state update from the light
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/STATE",
        (
            '{"POWER":"ON","Dimmer":50,'
            ' "Color":"0,255,0","HSBColor":"120,100,50","White":0}'
        ),
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("rgb_color") == (0, 255, 0)

    # Set color of the light from 0,255,0 to 255,0,0 @ 50%: Speed should be 6*2*2=24
    await common.async_turn_on(
        hass, "light.tasmota_test", rgb_color=[255, 0, 0], transition=6
    )
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        (
            "NoDelay;Fade2 1;NoDelay;Speed2 24;NoDelay;Power1 ON;NoDelay;HsbColor1"
            " 0;NoDelay;HsbColor2 100"
        ),
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Fake state update from the light
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/STATE",
        '{"POWER":"ON","Dimmer":100, "Color":"0,255,0","HSBColor":"120,100,50"}',
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("rgb_color") == (0, 255, 0)

    # Set color of the light from 0,255,0 to 255,0,0 @ 100%: Speed should be 6*2=12
    await common.async_turn_on(
        hass, "light.tasmota_test", rgb_color=[255, 0, 0], transition=6
    )
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        (
            "NoDelay;Fade2 1;NoDelay;Speed2 12;NoDelay;Power1 ON;NoDelay;HsbColor1"
            " 0;NoDelay;HsbColor2 100"
        ),
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Fake state update from the light
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/STATE",
        '{"POWER":"ON","Dimmer":50, "CT":153, "White":50}',
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_temp_kelvin") == 6535

    # Set color_temp of the light from 153 to 500 @ 50%: Speed should be 6*2*2=24
    await common.async_turn_on(
        hass, "light.tasmota_test", color_temp_kelvin=2000, transition=6
    )
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 24;NoDelay;Power1 ON;NoDelay;CT 500",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Fake state update from the light
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON","Dimmer":50, "CT":500}'
    )
    state = hass.states.get("light.tasmota_test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_temp_kelvin") == 2000

    # Set color_temp of the light from 500 to 326 @ 50%: Speed should be 6*2*2*2=48->40
    await common.async_turn_on(
        hass, "light.tasmota_test", color_temp_kelvin=3067, transition=6
    )
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/Backlog",
        "NoDelay;Fade2 1;NoDelay;Speed2 40;NoDelay;Power1 ON;NoDelay;CT 326",
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()