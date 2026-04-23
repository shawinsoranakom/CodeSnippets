async def test_subentry_reconfigure_edit_entity_multi_entitites(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mock_reload_after_entry_update: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    user_input_mqtt: dict[str, Any],
) -> None:
    """Test the subentry ConfigFlow reconfigure with multi entities."""
    await mqtt_mock_entry()
    config_entry: MockConfigEntry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    subentry_id: str
    subentry: ConfigSubentry
    subentry_id, subentry = next(iter(config_entry.subentries.items()))
    result = await config_entry.start_subentry_reconfigure_flow(hass, subentry_id)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "summary_menu"

    # assert we have a device for the subentry
    device = device_registry.async_get_device(identifiers={(mqtt.DOMAIN, subentry_id)})
    assert device is not None

    # assert we have an entity for all subentry components
    components = deepcopy(dict(subentry.data))["components"]
    assert len(components) == 2
    object_list = list(components)
    component_list = list(components.values())
    entity_name_0 = (
        f"{device.name} {component_list[0]['name']} ({component_list[0]['platform']})"
    )
    entity_name_1 = (
        f"{device.name} {component_list[1]['name']} ({component_list[1]['platform']})"
    )

    for key in components:
        unique_entity_id = f"{subentry_id}_{key}"
        entity_id = entity_registry.async_get_entity_id(
            domain="notify", platform=mqtt.DOMAIN, unique_id=unique_entity_id
        )
        assert entity_id is not None
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry is not None
        assert entity_entry.config_subentry_id == subentry_id

    # assert menu options, we have the option to delete one entity
    # we have no option to save and finish yet
    assert result["menu_options"] == [
        "entity",
        "update_entity",
        "delete_entity",
        "device",
        "availability",
        "export",
    ]

    # assert we can update an entity
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "update_entity"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "update_entity"
    assert result["data_schema"].schema["component"].config["options"] == [
        {"value": object_list[0], "label": entity_name_0},
        {"value": object_list[1], "label": entity_name_1},
    ]
    # select second entity
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "component": object_list[1],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity"

    # submit the common entity data with changed entity_picture
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "entity_picture": "https://example.com",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity_platform_config"

    # submit the platform specific entity data with changed entity_category
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "entity_category": "config",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mqtt_platform_config"

    # submit the new platform specific entity data
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input=user_input_mqtt,
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "summary_menu"

    # finish reconfigure flow
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "save_changes"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Check we still have our components
    new_components = deepcopy(dict(subentry.data))["components"]

    # Check the second component was updated
    assert new_components[object_list[0]] == components[object_list[0]]
    for key, value in user_input_mqtt.items():
        assert new_components[object_list[1]][key] == value

    # Assert the entry is reloaded to set up the entity
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(mock_reload_after_entry_update.mock_calls) == 1