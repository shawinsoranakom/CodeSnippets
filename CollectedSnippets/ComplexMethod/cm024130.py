async def test_reload_config_entry(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test manual entities reloaded and set up correctly."""
    await mqtt_mock_entry()

    # set up item through discovery
    config_discovery = {
        "name": "test_discovery",
        "unique_id": "test_discovery_unique456",
        "state_topic": "test-topic_discovery",
    }
    async_fire_mqtt_message(
        hass, "homeassistant/sensor/bla/config", json.dumps(config_discovery)
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.test_discovery") is not None

    entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]

    @callback
    def _check_entities() -> int:
        entities: list[Entity] = []
        mqtt_platforms = async_get_platforms(hass, mqtt.DOMAIN)
        for mqtt_platform in mqtt_platforms:
            assert mqtt_platform.config_entry is entry
            entities += (entity for entity in mqtt_platform.entities.values())

        return len(entities)

    # assert on initial set up manual items

    async_fire_mqtt_message(hass, "test-topic_manual1", "manual1_intial")
    async_fire_mqtt_message(hass, "test-topic_manual3", "manual3_intial")

    assert (state := hass.states.get("sensor.test_manual1")) is not None
    assert state.attributes["friendly_name"] == "test_manual1"
    assert state.state == "manual1_intial"
    assert (state := hass.states.get("sensor.test_manual3")) is not None
    assert state.attributes["friendly_name"] == "test_manual3"
    assert state.state == "manual3_intial"
    assert _check_entities() == 3

    # Reload the entry with a new configuration.yaml
    # Mock configuration.yaml was updated
    # The first item was updated, a new item was added, an item was removed
    hass_config_new = {
        "mqtt": {
            "sensor": [
                {
                    "name": "test_manual1_updated",
                    "unique_id": "test_manual_unique_id123",
                    "state_topic": "test-topic_manual1_updated",
                },
                {
                    "name": "test_manual2_new",
                    "unique_id": "test_manual_unique_id456",
                    "state_topic": "test-topic_manual2",
                },
            ]
        }
    }
    with patch(
        "homeassistant.config.load_yaml_config_file", return_value=hass_config_new
    ):
        assert await hass.config_entries.async_reload(entry.entry_id)
        assert entry.state is ConfigEntryState.LOADED
        await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.test_manual1")) is not None
    assert state.attributes["friendly_name"] == "test_manual1_updated"
    assert state.state == STATE_UNKNOWN
    assert (state := hass.states.get("sensor.test_manual2_new")) is not None
    assert state.attributes["friendly_name"] == "test_manual2_new"
    assert state.state is STATE_UNKNOWN
    # State of test_manual3 is still loaded but is unavailable
    assert (state := hass.states.get("sensor.test_manual3")) is not None
    assert state.state is STATE_UNAVAILABLE
    assert (state := hass.states.get("sensor.test_discovery")) is not None
    assert state.state is STATE_UNAVAILABLE
    # The entity is not loaded anymore
    assert _check_entities() == 2

    async_fire_mqtt_message(hass, "test-topic_manual1_updated", "manual1_update")
    async_fire_mqtt_message(hass, "test-topic_manual2", "manual2_update")
    async_fire_mqtt_message(hass, "test-topic_manual3", "manual3_update")

    assert (state := hass.states.get("sensor.test_manual1")) is not None
    assert state.state == "manual1_update"
    assert (state := hass.states.get("sensor.test_manual2_new")) is not None
    assert state.state == "manual2_update"
    assert (state := hass.states.get("sensor.test_manual3")) is not None
    assert state.state is STATE_UNAVAILABLE

    # Reload manual configured items and assert again
    with patch(
        "homeassistant.config.load_yaml_config_file", return_value=hass_config_new
    ):
        await hass.services.async_call(
            "mqtt",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.test_manual1")) is not None
    assert state.attributes["friendly_name"] == "test_manual1_updated"
    assert state.state == STATE_UNKNOWN
    assert (state := hass.states.get("sensor.test_manual2_new")) is not None
    assert state.attributes["friendly_name"] == "test_manual2_new"
    assert state.state == STATE_UNKNOWN
    assert (state := hass.states.get("sensor.test_manual3")) is not None
    assert state.state == STATE_UNAVAILABLE
    assert _check_entities() == 2

    async_fire_mqtt_message(
        hass, "test-topic_manual1_updated", "manual1_update_after_reload"
    )
    async_fire_mqtt_message(hass, "test-topic_manual2", "manual2_update_after_reload")
    async_fire_mqtt_message(hass, "test-topic_manual3", "manual3_update_after_reload")

    assert (state := hass.states.get("sensor.test_manual1")) is not None
    assert state.state == "manual1_update_after_reload"
    assert (state := hass.states.get("sensor.test_manual2_new")) is not None
    assert state.state == "manual2_update_after_reload"
    assert (state := hass.states.get("sensor.test_manual3")) is not None
    assert state.state is STATE_UNAVAILABLE