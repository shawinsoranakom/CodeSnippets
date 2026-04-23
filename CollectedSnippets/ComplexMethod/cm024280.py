async def test_subentry_reconfigure_edit_entity_single_entity(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    user_input_platform_config_validation: tuple[
        tuple[dict[str, Any], dict[str, str] | None], ...
    ]
    | None,
    user_input_platform_config: dict[str, Any],
    user_input_mqtt: dict[str, Any],
    component_data: dict[str, Any],
    removed_options: tuple[str, ...],
) -> None:
    """Test the subentry ConfigFlow reconfigure with single entity."""
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

    # assert we have an entity for the subentry component
    # Check we have "notify_milkman_alert" in our mock data
    components = deepcopy(dict(subentry.data))["components"]
    assert len(components) == 1

    component_id, component = next(iter(components.items()))

    unique_entity_id = f"{subentry_id}_{component_id}"
    entity_id = entity_registry.async_get_entity_id(
        domain=component["platform"], platform=mqtt.DOMAIN, unique_id=unique_entity_id
    )
    assert entity_id is not None
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry is not None
    assert entity_entry.config_subentry_id == subentry_id

    # assert menu options, we do not have the option to delete an entity
    # we have no option to save and finish yet
    assert result["menu_options"] == [
        "entity",
        "update_entity",
        "device",
        "availability",
        "export",
    ]

    # assert we can update the entity, there is no select step
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "update_entity"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "entity"

    # submit the new common entity data, reset entity_picture
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.FORM

    # entity platform config flow step
    assert result["step_id"] == "entity_platform_config"
    for entity_validation_config, errors in user_input_platform_config_validation:
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            user_input=entity_validation_config,
        )
        assert result["step_id"] == "entity_platform_config"
        assert result.get("errors") == errors
        assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input=user_input_platform_config,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mqtt_platform_config"

    # submit the new platform specific entity data,
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

    # Check we still have out components
    new_components = deepcopy(dict(subentry.data))["components"]
    assert len(new_components) == 1

    # Check our update was successful
    assert "entity_picture" not in new_components[component_id]

    # Check the second component was updated
    for key, value in component_data.items():
        assert new_components[component_id][key] == value

    assert set(component) - set(new_components[component_id]) == removed_options