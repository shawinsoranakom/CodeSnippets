async def test_controlling_state_via_mqtt_inverted(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota, tilt
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 3
    config["rl"][1] = 3
    config["sho"] = [1]  # Inverted cover
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
    assert state.attributes["supported_features"] == COVER_SUPPORT

    # Periodic updates
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":54,"Direction":-1' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "opening"
    assert state.attributes["current_position"] == 46

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":100,"Direction":1' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closing"
    assert state.attributes["current_position"] == 0

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":0,"Direction":0' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 100

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":99,"Direction":0' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 1

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/tele/SENSOR",
        '{"Shutter1":{"Position":100,"Direction":0' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closed"
    assert state.attributes["current_position"] == 0

    # State poll response
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":54,"Direction":-1' + tilt + "}}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "opening"
    assert state.attributes["current_position"] == 46

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":100,"Direction":1' + tilt + "}}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closing"
    assert state.attributes["current_position"] == 0

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":0,"Direction":0' + tilt + "}}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 100

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":99,"Direction":0' + tilt + "}}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 1

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS10",
        '{"StatusSNS":{"Shutter1":{"Position":100,"Direction":0' + tilt + "}}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closed"
    assert state.attributes["current_position"] == 0

    # Command response
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":54,"Direction":-1' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "opening"
    assert state.attributes["current_position"] == 46

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":100,"Direction":1' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closing"
    assert state.attributes["current_position"] == 0

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":0,"Direction":0' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 100

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":1,"Direction":0' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "open"
    assert state.attributes["current_position"] == 99

    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/RESULT",
        '{"Shutter1":{"Position":100,"Direction":0' + tilt + "}}",
    )
    state = hass.states.get("cover.tasmota_cover_1")
    assert state.state == "closed"
    assert state.attributes["current_position"] == 0