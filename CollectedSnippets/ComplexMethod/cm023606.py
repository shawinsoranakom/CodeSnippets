async def test_single_shot_status_sensor_state_via_mqtt(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mqtt_mock: MqttMockHAClient,
    setup_tasmota,
) -> None:
    """Test state update via MQTT."""
    # Pre-enable the status sensor
    entity_registry.async_get_or_create(
        Platform.SENSOR,
        "tasmota",
        "00000049A3BC_status_sensor_status_sensor_status_restart_reason",
        suggested_object_id="tasmota_status",
        disabled_by=None,
    )

    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Test polled state update
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS1",
        '{"StatusPRM":{"RestartReason":"Some reason"}}',
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "Some reason"

    # Test polled state update is ignored
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS1",
        '{"StatusPRM":{"RestartReason":"Another reason"}}',
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "Some reason"

    # Device signals online again
    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "Some reason"

    # Test polled state update
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS1",
        '{"StatusPRM":{"RestartReason":"Another reason"}}',
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "Another reason"

    # Test polled state update is ignored
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS1",
        '{"StatusPRM":{"RestartReason":"Third reason"}}',
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "Another reason"