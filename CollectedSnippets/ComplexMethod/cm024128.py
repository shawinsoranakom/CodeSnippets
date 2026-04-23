async def test_unload_config_entry(
    hass: HomeAssistant,
    mqtt_client_mock: MqttMockPahoClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test unloading the MQTT entry."""
    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={mqtt.CONF_BROKER: "test-broker"},
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)

    assert await async_setup_component(hass, mqtt.DOMAIN, {})
    assert hass.services.has_service(mqtt.DOMAIN, "dump")
    assert hass.services.has_service(mqtt.DOMAIN, "publish")

    mqtt_config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    assert mqtt_config_entry.state is ConfigEntryState.LOADED

    # Publish just before unloading to test await cleanup
    mqtt_client_mock.reset_mock()
    mqtt.publish(hass, "just_in_time", "published", qos=0, retain=False)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mqtt_config_entry.entry_id)
    new_mqtt_config_entry = mqtt_config_entry
    mqtt_client_mock.publish.assert_any_call("just_in_time", "published", 0, False)
    assert new_mqtt_config_entry.state is ConfigEntryState.NOT_LOADED
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.services.has_service(mqtt.DOMAIN, "dump")
    assert hass.services.has_service(mqtt.DOMAIN, "publish")
    assert "No ACK from MQTT server" not in caplog.text