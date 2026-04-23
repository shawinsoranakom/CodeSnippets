async def test_invalid_discovery_prefix(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mock_try_connection: MagicMock,
    mock_reload_after_entry_update: MagicMock,
) -> None:
    """Test setting an invalid discovery prefix."""
    mqtt_mock = await mqtt_mock_entry()
    mock_try_connection.return_value = True
    config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 1234,
        },
        options={
            mqtt.CONF_DISCOVERY: True,
            mqtt.CONF_DISCOVERY_PREFIX: "homeassistant",
        },
    )
    await hass.async_block_till_done()
    mock_reload_after_entry_update.reset_mock()
    mqtt_mock.async_connect.reset_mock()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"

    await hass.async_block_till_done()
    assert mqtt_mock.async_connect.call_count == 0

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_DISCOVERY: True,
            mqtt.CONF_DISCOVERY_PREFIX: "homeassistant#invalid",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    assert result["errors"]["base"] == "bad_discovery_prefix"
    assert config_entry.data == {
        mqtt.CONF_BROKER: "test-broker",
        CONF_PORT: 1234,
    }
    assert config_entry.options == {
        mqtt.CONF_DISCOVERY: True,
        mqtt.CONF_DISCOVERY_PREFIX: "homeassistant",
    }

    await hass.async_block_till_done()
    # assert that the entry was not reloaded with the new config
    assert mock_reload_after_entry_update.call_count == 0