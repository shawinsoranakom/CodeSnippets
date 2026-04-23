async def test_subentry_reconfigure_update_device_properties(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the subentry ConfigFlow reconfigure and update device properties."""
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

    # Assert initial data
    device = deepcopy(dict(subentry.data))["device"]
    assert device["name"] == "Milk notifier"
    assert device["sw_version"] == "1.0"
    assert device["hw_version"] == "2.1 rev a"
    assert device["model"] == "Model XL"
    assert device["model_id"] == "mn002"

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

    # assert we can update the device properties
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "device"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    # Update the device details
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "Beer notifier",
            "advanced_settings": {"sw_version": "1.1"},
            "model": "Beer bottle XL",
            "model_id": "bn003",
            "manufacturer": "Beer Masters",
            "configuration_url": "https://example.com",
            "mqtt_settings": {"qos": 1},
        },
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

    # Check our device and mqtt data was updated correctly
    device = deepcopy(dict(subentry.data))["device"]
    assert device["name"] == "Beer notifier"
    assert "hw_version" not in device
    assert device["model"] == "Beer bottle XL"
    assert device["model_id"] == "bn003"
    assert device["sw_version"] == "1.1"
    assert device["manufacturer"] == "Beer Masters"
    assert device["mqtt_settings"]["qos"] == 1
    assert "qos" not in device