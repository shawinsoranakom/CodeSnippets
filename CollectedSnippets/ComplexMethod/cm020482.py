async def test_button_exists_with_deprecation(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    mocked_feature_button: Feature,
    entity_disabled: bool,
    entity_has_automations: bool,
) -> None:
    """Test the deprecated buttons are deleted or raise issues."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)

    object_id = "my_device_test_alarm"
    entity_id = f"button.{object_id}"
    unique_id = f"{DEVICE_ID}_test_alarm"
    issue_id = f"deprecated_entity_{entity_id}_automation.test_automation"

    if entity_has_automations:
        await setup_automation(hass, "test_automation", entity_id)

    entity = entity_registry.async_get_or_create(
        domain=BUTTON_DOMAIN,
        platform=DOMAIN,
        unique_id=unique_id,
        suggested_object_id=object_id,
        config_entry=config_entry,
        disabled_by=er.RegistryEntryDisabler.USER if entity_disabled else None,
    )
    assert entity.entity_id == entity_id
    assert not hass.states.get(entity_id)

    mocked_feature = mocked_feature_button
    dev = _mocked_device(alias="my_device", features=[mocked_feature])
    with _patch_discovery(device=dev), _patch_connect(device=dev):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entity = entity_registry.async_get(entity_id)
    # entity and state will be none if removed from registry
    assert (entity is None) == entity_disabled
    assert (hass.states.get(entity_id) is None) == entity_disabled

    assert (
        issue_registry.async_get_issue(DOMAIN, issue_id) is not None
    ) == entity_has_automations