async def test_subentry_reconfigure_export_settings(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    device_registry: dr.DeviceRegistry,
    flow_step: str,
    field_suggestions: dict[str, str],
) -> None:
    """Test the subentry ConfigFlow reconfigure export feature."""
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

    # assert we entity for all subentry components
    components = deepcopy(dict(subentry.data))["components"]
    assert len(components) == 2

    # assert menu options, we have the option to export
    assert result["menu_options"] == [
        "entity",
        "update_entity",
        "delete_entity",
        "device",
        "availability",
        "export",
    ]

    # Open export menu
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "export"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "export"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": flow_step},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == flow_step
    assert result["description_placeholders"] == {
        "url": "https://www.home-assistant.io/integrations/mqtt/"
    }

    # Assert the export is correct
    for field in result["data_schema"].schema:
        assert (
            field_suggestions[field].format(subentry_id)
            in field.description["suggested_value"]
        )

    # Back to summary menu
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "summary_menu"