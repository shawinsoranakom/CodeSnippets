async def test_migrate_config_entry(
    hass: HomeAssistant,
    switch_old_id_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration of config entry. Only migrates switches to a new unique_id."""
    switch: er.RegistryEntry = entity_registry.async_get_or_create(
        domain="switch",
        platform="vesync",
        unique_id="switch",
        config_entry=switch_old_id_config_entry,
        suggested_object_id="switch",
    )

    humidifier: er.RegistryEntry = entity_registry.async_get_or_create(
        domain="humidifier",
        platform="vesync",
        unique_id="humidifier",
        config_entry=switch_old_id_config_entry,
        suggested_object_id="humidifier",
    )

    assert switch.unique_id == "switch"
    assert switch_old_id_config_entry.minor_version == 1
    assert humidifier.unique_id == "humidifier"

    await hass.config_entries.async_setup(switch_old_id_config_entry.entry_id)
    await hass.async_block_till_done()

    assert switch_old_id_config_entry.minor_version == 3

    migrated_switch = entity_registry.async_get(switch.entity_id)
    assert migrated_switch is not None
    assert migrated_switch.entity_id.startswith("switch")
    assert migrated_switch.unique_id == "switch-device_status"
    # Confirm humidifier was not impacted
    migrated_humidifier = entity_registry.async_get(humidifier.entity_id)
    assert migrated_humidifier is not None
    assert migrated_humidifier.unique_id == "humidifier"

    # Assert that entity exists in the switch domain
    switch_entities = [
        e for e in entity_registry.entities.values() if e.domain == "switch"
    ]
    assert len(switch_entities) == 3

    humidifier_entities = [
        e for e in entity_registry.entities.values() if e.domain == "humidifier"
    ]
    assert len(humidifier_entities) == 2
    assert switch_old_id_config_entry.version == 1
    assert switch_old_id_config_entry.unique_id == "TESTACCOUNTID"