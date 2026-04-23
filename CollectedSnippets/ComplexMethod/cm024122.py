async def test_reload_entry_with_restored_subscriptions(
    hass: HomeAssistant,
    mock_debouncer: asyncio.Event,
    record_calls: MessageCallbackType,
    recorded_calls: list[ReceiveMessage],
) -> None:
    """Test reloading the config entry with with subscriptions restored."""
    # Setup the MQTT entry
    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={mqtt.CONF_BROKER: "test-broker"},
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    hass.config.components.add(mqtt.DOMAIN)
    with patch("homeassistant.config.load_yaml_config_file", return_value={}):
        await hass.config_entries.async_setup(entry.entry_id)

    mock_debouncer.clear()
    await mqtt.async_subscribe(hass, "test-topic", record_calls)
    await mqtt.async_subscribe(hass, "wild/+/card", record_calls)
    # cooldown
    await mock_debouncer.wait()

    async_fire_mqtt_message(hass, "test-topic", "test-payload")
    async_fire_mqtt_message(hass, "wild/any/card", "wild-card-payload")

    assert len(recorded_calls) == 2
    assert recorded_calls[0].topic == "test-topic"
    assert recorded_calls[0].payload == "test-payload"
    assert recorded_calls[1].topic == "wild/any/card"
    assert recorded_calls[1].payload == "wild-card-payload"
    recorded_calls.clear()

    # Reload the entry
    with patch("homeassistant.config.load_yaml_config_file", return_value={}):
        assert await hass.config_entries.async_reload(entry.entry_id)
        mock_debouncer.clear()
        assert entry.state is ConfigEntryState.LOADED
        # cooldown
        await mock_debouncer.wait()

    async_fire_mqtt_message(hass, "test-topic", "test-payload2")
    async_fire_mqtt_message(hass, "wild/any/card", "wild-card-payload2")

    assert len(recorded_calls) == 2
    assert recorded_calls[0].topic == "test-topic"
    assert recorded_calls[0].payload == "test-payload2"
    assert recorded_calls[1].topic == "wild/any/card"
    assert recorded_calls[1].payload == "wild-card-payload2"
    recorded_calls.clear()

    # Reload the entry again
    with patch("homeassistant.config.load_yaml_config_file", return_value={}):
        assert await hass.config_entries.async_reload(entry.entry_id)
        mock_debouncer.clear()
        assert entry.state is ConfigEntryState.LOADED
        # cooldown
        await mock_debouncer.wait()

    async_fire_mqtt_message(hass, "test-topic", "test-payload3")
    async_fire_mqtt_message(hass, "wild/any/card", "wild-card-payload3")

    assert len(recorded_calls) == 2
    assert recorded_calls[0].topic == "test-topic"
    assert recorded_calls[0].payload == "test-payload3"
    assert recorded_calls[1].topic == "wild/any/card"
    assert recorded_calls[1].payload == "wild-card-payload3"