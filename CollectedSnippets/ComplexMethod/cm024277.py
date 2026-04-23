async def test_subentry_configflow(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mock_reload_after_entry_update: MagicMock,
    config_subentries_data: dict[str, Any],
    mock_device_user_input: dict[str, Any],
    mock_entity_user_input: dict[str, Any],
    mock_entity_details_user_input: dict[str, Any],
    mock_entity_details_failed_user_input: tuple[
        tuple[dict[str, Any], dict[str, str]],
    ],
    mock_mqtt_user_input: dict[str, Any],
    mock_failed_mqtt_user_input: tuple[tuple[dict[str, Any], dict[str, str]],],
    entity_name: str,
) -> None:
    """Test the subentry ConfigFlow."""
    device_name = mock_device_user_input["name"]
    component = next(iter(config_subentries_data["components"].values()))

    await mqtt_mock_entry()
    config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "device"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    # Test the URL validation
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": device_name,
            "configuration_url": "http:/badurl.example.com",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"
    assert result["errors"]["configuration_url"] == "invalid_url"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input=mock_device_user_input,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity"
    assert result["errors"] == {}
    assert "description_placeholders" in result
    for placeholder, translation in TRANSLATION_DESCRIPTION_PLACEHOLDERS.items():
        assert placeholder in result["description_placeholders"]
        assert result["description_placeholders"][placeholder] == translation

    # Process entity flow (initial step)

    # Test the entity picture URL validation
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "platform": component["platform"],
            "entity_picture": "invalid url",
        }
        | mock_entity_user_input,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity"

    # Try again with valid data
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "platform": component["platform"],
            "entity_picture": component["entity_picture"],
        }
        | mock_entity_user_input,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert (
        result["description_placeholders"]
        == {
            "mqtt_device": device_name,
            "platform": component["platform"],
            "entity": entity_name,
            "url": learn_more_url(component["platform"]),
        }
        | TRANSLATION_DESCRIPTION_PLACEHOLDERS
    )

    # Process entity details step
    assert result["step_id"] == "entity_platform_config"

    # First test validators if set of test
    for failed_user_input, failed_errors in mock_entity_details_failed_user_input:
        # Test an invalid entity details user input case
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input=failed_user_input,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == failed_errors

    # Now try again with valid data
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input=mock_entity_details_user_input,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert (
        result["description_placeholders"]
        == {
            "mqtt_device": device_name,
            "platform": component["platform"],
            "entity": entity_name,
            "url": learn_more_url(component["platform"]),
        }
        | TRANSLATION_DESCRIPTION_PLACEHOLDERS
    )

    # Process mqtt platform config flow
    # Test an invalid mqtt user input case
    for failed_user_input, failed_errors in mock_failed_mqtt_user_input:
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input=failed_user_input,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == failed_errors

    # Try again with a valid configuration
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input=mock_mqtt_user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == device_name

    subentry_component = next(
        iter(next(iter(config_entry.subentries.values())).data["components"].values())
    )
    assert subentry_component == next(
        iter(config_subentries_data["components"].values())
    )

    subentry_device_data = next(iter(config_entry.subentries.values())).data["device"]
    for option, value in mock_device_user_input.items():
        assert subentry_device_data[option] == value

    await hass.async_block_till_done()
    await hass.async_block_till_done(wait_background_tasks=True)

    # Assert the entry is reloaded to set up the entity
    assert len(mock_reload_after_entry_update.mock_calls) == 1