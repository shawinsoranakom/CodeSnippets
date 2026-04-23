async def test_enable_status_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mqtt_mock: MqttMockHAClient,
    setup_tasmota,
) -> None:
    """Test enabling status sensor."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.tasmota_signal")
    assert state is None
    entry = entity_registry.async_get("sensor.tasmota_signal")
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # Enable the signal level status sensor
    updated_entry = entity_registry.async_update_entity(
        "sensor.tasmota_signal", disabled_by=None
    )
    assert updated_entry != entry
    assert updated_entry.disabled is False
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow()
        + timedelta(seconds=config_entries.RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # Fake re-send of retained discovery message
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.tasmota_signal")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    state = hass.states.get("sensor.tasmota_signal")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)