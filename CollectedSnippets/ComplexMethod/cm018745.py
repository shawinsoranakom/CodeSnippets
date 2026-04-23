async def test_deprecated_sensor_issue_lifecycle(
    hass: HomeAssistant,
    issue_registry: IssueRegistry,
    entity_registry: er.EntityRegistry,
    mock_integration: MockConfigEntry,
) -> None:
    """Test deprecated sensor cleanup and issue lifecycle."""
    sensor_unique_id = f"{format_mac(MOCK_MAC)}_hdr_processing"
    issue_id = f"deprecated_sensor_{mock_integration.entry_id}_hdr_processing"

    assert (
        entity_registry.async_get_entity_id(Platform.SENSOR, DOMAIN, sensor_unique_id)
        is None
    )
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None

    sensor_entry = entity_registry.async_get_or_create(
        Platform.SENSOR,
        DOMAIN,
        sensor_unique_id,
        config_entry=mock_integration,
        suggested_object_id="jvc_projector_hdr_processing",
        disabled_by=er.RegistryEntryDisabler.INTEGRATION,
    )
    entity_id = sensor_entry.entity_id

    with patch(
        "homeassistant.components.jvc_projector.util.get_automations_and_scripts_using_entity",
        return_value=["- [Test Automation](/config/automation/edit/test_automation)"],
    ):
        await hass.config_entries.async_reload(mock_integration.entry_id)
        await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "deprecated_sensor_scripts"
    assert entity_registry.async_get(entity_id) is not None

    await hass.config_entries.async_reload(mock_integration.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get(entity_id) is None
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None