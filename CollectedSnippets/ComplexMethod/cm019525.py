async def test_binary_sensor_exists_with_deprecation(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_ring_client: Ring,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    entity_disabled: bool,
    entity_has_automations: bool,
) -> None:
    """Test the deprecated Ring binary sensors are deleted or raise issues."""
    mock_config_entry.add_to_hass(hass)

    entity_id = "binary_sensor.front_door_motion"
    unique_id = f"{FRONT_DOOR_DEVICE_ID}-motion"
    issue_id = f"deprecated_entity_{entity_id}_automation.test_automation"

    if entity_has_automations:
        await setup_automation(hass, "test_automation", entity_id)

    entity = entity_registry.async_get_or_create(
        domain=BINARY_SENSOR_DOMAIN,
        platform=DOMAIN,
        unique_id=unique_id,
        suggested_object_id="front_door_motion",
        config_entry=mock_config_entry,
        disabled_by=er.RegistryEntryDisabler.USER if entity_disabled else None,
    )
    assert entity.entity_id == entity_id
    assert not hass.states.get(entity_id)
    with patch("homeassistant.components.ring.PLATFORMS", [Platform.BINARY_SENSOR]):
        assert await async_setup_component(hass, DOMAIN, {})

    entity = entity_registry.async_get(entity_id)
    # entity and state will be none if removed from registry
    assert (entity is None) == entity_disabled
    assert (hass.states.get(entity_id) is None) == entity_disabled

    assert (
        issue_registry.async_get_issue(DOMAIN, issue_id) is not None
    ) == entity_has_automations