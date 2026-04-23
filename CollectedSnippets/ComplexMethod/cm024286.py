async def test_subentry_configflow_section_feature(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test the subentry ConfigFlow sections are hidden when they have no configurable options."""
    await mqtt_mock_entry()
    config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "device"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={"name": "Bla", "mqtt_settings": {"qos": 1}},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={"platform": "fan"},
    )
    assert result["type"] is FlowResultType.FORM
    assert (
        result["description_placeholders"]
        == {
            "mqtt_device": "Bla",
            "platform": "fan",
            "entity": "Bla",
            "url": learn_more_url("fan"),
        }
        | TRANSLATION_DESCRIPTION_PLACEHOLDERS
    )

    # Process entity details step
    assert result["step_id"] == "entity_platform_config"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={"fan_feature_speed": True},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "mqtt_platform_config"

    # Check mqtt platform config flow sections from data schema
    data_schema = result["data_schema"].schema
    assert "fan_speed_settings" in data_schema
    assert "fan_preset_mode_settings" not in data_schema