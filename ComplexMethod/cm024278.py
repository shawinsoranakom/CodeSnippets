async def test_subentry_reconfigure_remove_entity(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the subentry ConfigFlow reconfigure removing an entity."""
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

    for key, component in components.items():
        unique_entity_id = f"{subentry_id}_{key}"
        entity_id = entity_registry.async_get_entity_id(
            domain=component["platform"],
            platform=mqtt.DOMAIN,
            unique_id=unique_entity_id,
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

    # assert we can delete an entity
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "delete_entity"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "delete_entity"
    assert result["data_schema"].schema["component"].config["options"] == [
        {"value": object_list[0], "label": entity_name_0},
        {"value": object_list[1], "label": entity_name_1},
    ]
    # remove notify_the_second_notifier
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "component": object_list[1],
        },
    )

    # assert menu options, we have only one item left, we cannot delete it
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "summary_menu"
    assert result["menu_options"] == [
        "entity",
        "update_entity",
        "device",
        "availability",
        "save_changes",
    ]

    # finish reconfigure flow
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "save_changes"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # check if the second entity was removed from the subentry and entity registry
    unique_entity_id = f"{subentry_id}_{object_list[1]}"
    entity_id = entity_registry.async_get_entity_id(
        domain=components[object_list[1]]["platform"],
        platform=mqtt.DOMAIN,
        unique_id=unique_entity_id,
    )
    assert entity_id is None
    new_components = deepcopy(dict(subentry.data))["components"]
    assert object_list[0] in new_components
    assert object_list[1] not in new_components