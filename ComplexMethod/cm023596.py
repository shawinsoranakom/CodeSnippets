async def test_off_delay(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_tasmota
) -> None:
    """Test off_delay option."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 13  # PUSHON: 1s off_delay
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    events = []

    @ha.callback
    def callback(event):
        """Verify event got called."""
        events.append(event.data["new_state"].state)

    hass.bus.async_listen(EVENT_STATE_CHANGED, callback)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    assert events == ["unknown"]
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"ON"}}'
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_ON
    assert events == ["unknown", "on"]

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"ON"}}'
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_ON
    assert events == ["unknown", "on", "on"]

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.tasmota_binary_sensor_1")
    assert state.state == STATE_OFF
    assert events == ["unknown", "on", "on", "off"]