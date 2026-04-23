async def test_disabling_and_enabling_entry(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test disabling and enabling the config entry."""
    await mqtt_mock_entry()
    entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED
    # Late discovery of a mqtt entity
    config_tag = '{"topic": "0AFFD2/tag_scanned", "value_template": "{{ value_json.PN532.UID }}"}'
    config_alarm_control_panel = '{"name": "test_new", "state_topic": "home/alarm", "command_topic": "home/alarm/set"}'
    config_light = '{"name": "test_new", "command_topic": "test-topic_new"}'

    with patch(
        "homeassistant.components.mqtt.entity.mqtt_config_entry_enabled",
        return_value=False,
    ):
        # Discovery of mqtt tag
        async_fire_mqtt_message(hass, "homeassistant/tag/abc/config", config_tag)

        # Late discovery of mqtt entities
        async_fire_mqtt_message(
            hass,
            "homeassistant/alarm_control_panel/abc/config",
            config_alarm_control_panel,
        )
        async_fire_mqtt_message(hass, "homeassistant/light/abc/config", config_light)

    # Disable MQTT config entry
    await hass.config_entries.async_set_disabled_by(
        entry.entry_id, ConfigEntryDisabler.USER
    )

    await hass.async_block_till_done()
    await hass.async_block_till_done()
    assert (
        "MQTT integration is disabled, skipping setup of discovered item MQTT tag"
        in caplog.text
    )
    assert (
        "MQTT integration is disabled, skipping setup of discovered item MQTT alarm_control_panel"
        in caplog.text
    )
    assert (
        "MQTT integration is disabled, skipping setup of discovered item MQTT light"
        in caplog.text
    )

    new_mqtt_config_entry = entry
    assert new_mqtt_config_entry.state is ConfigEntryState.NOT_LOADED

    # Enable the entry again
    await hass.config_entries.async_set_disabled_by(entry.entry_id, None)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    new_mqtt_config_entry = entry
    assert new_mqtt_config_entry.state is ConfigEntryState.LOADED

    assert hass.states.get("light.test") is not None
    assert hass.states.get("alarm_control_panel.test") is not None