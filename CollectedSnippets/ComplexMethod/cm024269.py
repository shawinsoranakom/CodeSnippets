async def test_disable_birth_will(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mock_try_connection: MagicMock,
    mock_reload_after_entry_update: MagicMock,
) -> None:
    """Test disabling birth and will."""
    await mqtt_mock_entry()
    mock_try_connection.return_value = True
    config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 1234,
        },
    )
    await hass.async_block_till_done()
    mock_reload_after_entry_update.reset_mock()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_DISCOVERY: True,
            mqtt.CONF_DISCOVERY_PREFIX: "homeassistant",
            "birth_enable": False,
            "birth_topic": "ha_state/online",
            "birth_payload": "online",
            "birth_qos": 1,
            "birth_retain": True,
            "will_enable": False,
            "will_topic": "ha_state/offline",
            "will_payload": "offline",
            "will_qos": 2,
            "will_retain": True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "birth_message": {},
        "discovery": True,
        "discovery_prefix": "homeassistant",
        "will_message": {},
    }
    assert config_entry.data == {mqtt.CONF_BROKER: "test-broker", CONF_PORT: 1234}
    assert config_entry.options == {
        mqtt.CONF_DISCOVERY: True,
        mqtt.CONF_DISCOVERY_PREFIX: "homeassistant",
        mqtt.CONF_BIRTH_MESSAGE: {},
        mqtt.CONF_WILL_MESSAGE: {},
    }

    await hass.async_block_till_done()
    # assert that the entry was reloaded with the new config
    assert mock_reload_after_entry_update.call_count == 1