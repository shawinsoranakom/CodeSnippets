async def test_status_sensor_state_via_mqtt(
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
        "00000049A3BC_status_sensor_status_sensor_status_signal",
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

    # Test pushed state update
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/tele/STATE", '{"Wifi":{"Signal":20.5}}'
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "20.5"

    # Test polled state update
    async_fire_mqtt_message(
        hass,
        "tasmota_49A3BC/stat/STATUS11",
        '{"StatusSTS":{"Wifi":{"Signal":20.0}}}',
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_status")
    assert state.state == "20.0"

    # Test force update flag
    entity = hass.data["entity_components"]["sensor"].get_entity(
        "sensor.tasmota_status"
    )
    assert not entity.force_update