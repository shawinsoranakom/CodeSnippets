async def test_controlling_state_via_mqtt_tilt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 3
    config["rl"][1] = 3
    config["sht"] = [[-90, 90, 24]]
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == STATE_UNKNOWN
    assert state.attributes["supported_features"] == COVER_SUPPORT | TILT_SUPPORT
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Periodic updates
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":54,"Direction":-1,"Tilt":-90}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closing"
    assert state.attributes["current_position"] == 54
    assert state.attributes["current_tilt_position"] == 0

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":100,"Direction":1,"Tilt":90}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "opening"
    assert state.attributes["current_position"] == 100
    assert state.attributes["current_tilt_position"] == 100

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":0,"Direction":0,"Tilt":0}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closed"
    assert state.attributes["current_position"] == 0
    assert state.attributes["current_tilt_position"] == 50

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/SENSOR", '{"Shutter1":{"Position":1,"Direction":0}}'
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 1

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":100,"Direction":0}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 100

    # State poll response
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":54,"Direction":-1,"Tilt":-90}}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closing"
    assert state.attributes["current_position"] == 54
    assert state.attributes["current_tilt_position"] == 0

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":100,"Direction":1,"Tilt":90}}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "opening"
    assert state.attributes["current_position"] == 100
    assert state.attributes["current_tilt_position"] == 100

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":0,"Direction":0,"Tilt":0}}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closed"
    assert state.attributes["current_position"] == 0
    assert state.attributes["current_tilt_position"] == 50

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":1,"Direction":0}}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 1

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":100,"Direction":0}}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 100

    # Command response
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":54,"Direction":-1,"Tilt":-90}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closing"
    assert state.attributes["current_position"] == 54
    assert state.attributes["current_tilt_position"] == 0

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":100,"Direction":1,"Tilt":90}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "opening"
    assert state.attributes["current_position"] == 100
    assert state.attributes["current_tilt_position"] == 100

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":0,"Direction":0,"Tilt":0}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closed"
    assert state.attributes["current_position"] == 0
    assert state.attributes["current_tilt_position"] == 50

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Shutter1":{"Position":1,"Direction":0}}'
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 1

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":100,"Direction":0}}',
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 100