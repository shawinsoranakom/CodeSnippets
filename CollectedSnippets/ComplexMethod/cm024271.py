async def test_option_flow_default_suggested_values(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mock_try_connection_success: MqttMockPahoClient,
) -> None:
    """Test config flow options has default/suggested values."""
    await mqtt_mock_entry()
    config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 1234,
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
        },
        options={
            mqtt.CONF_DISCOVERY: True,
            mqtt.CONF_BIRTH_MESSAGE: {
                mqtt.ATTR_TOPIC: "ha_state/online",
                mqtt.ATTR_PAYLOAD: "online",
                mqtt.ATTR_QOS: 1,
                mqtt.ATTR_RETAIN: True,
            },
            mqtt.CONF_WILL_MESSAGE: {
                mqtt.ATTR_TOPIC: "ha_state/offline",
                mqtt.ATTR_PAYLOAD: "offline",
                mqtt.ATTR_QOS: 2,
                mqtt.ATTR_RETAIN: False,
            },
        },
    )
    await hass.async_block_till_done()

    # Test default/suggested values from config
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    defaults = {
        "birth_qos": 1,
        "birth_retain": True,
        "will_qos": 2,
        "will_retain": False,
    }
    suggested = {
        "birth_topic": "ha_state/online",
        "birth_payload": "online",
        "will_topic": "ha_state/offline",
        "will_payload": "offline",
    }
    for key, value in defaults.items():
        assert get_default(result["data_schema"].schema, key) == value
    for key, value in suggested.items():
        assert get_schema_suggested_value(result["data_schema"].schema, key) == value

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "birth_topic": "ha_state/onl1ne",
            "birth_payload": "onl1ne",
            "birth_qos": 2,
            "birth_retain": False,
            "will_topic": "ha_state/offl1ne",
            "will_payload": "offl1ne",
            "will_qos": 1,
            "will_retain": True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Test updated default/suggested values from config
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    defaults = {
        "birth_qos": 2,
        "birth_retain": False,
        "will_qos": 1,
        "will_retain": True,
    }
    suggested = {
        "birth_topic": "ha_state/onl1ne",
        "birth_payload": "onl1ne",
        "will_topic": "ha_state/offl1ne",
        "will_payload": "offl1ne",
    }
    for key, value in defaults.items():
        assert get_default(result["data_schema"].schema, key) == value
    for key, value in suggested.items():
        assert get_schema_suggested_value(result["data_schema"].schema, key) == value

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "birth_topic": "ha_state/onl1ne",
            "birth_payload": "onl1ne",
            "birth_qos": 2,
            "birth_retain": False,
            "will_topic": "ha_state/offl1ne",
            "will_payload": "offl1ne",
            "will_qos": 1,
            "will_retain": True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Make sure all MQTT related jobs are done before ending the test
    await hass.async_block_till_done()