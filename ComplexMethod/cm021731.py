async def test_migrate_entity_unique_ids(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry_v1_1: MockConfigEntry,
) -> None:
    """Test migration of entity unique IDs."""
    mock_config_entry_v1_1.add_to_hass(hass)

    # Create entities with old unique ID format
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "TEST123456789_ofa_orp_value",
        config_entry=mock_config_entry_v1_1,
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "TEST123456789_ofa_ph_value",
        config_entry=mock_config_entry_v1_1,
    )
    # Create entity with correct unique ID that should not be changed
    unchanged_entity = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "TEST123456789_orp",
        config_entry=mock_config_entry_v1_1,
    )

    assert mock_config_entry_v1_1.version == 1
    assert mock_config_entry_v1_1.minor_version == 1

    # Setup the integration - this will trigger migration
    await hass.config_entries.async_setup(mock_config_entry_v1_1.entry_id)
    await hass.async_block_till_done()

    # Verify the config entry version was updated from 1.1 to 1.2
    assert mock_config_entry_v1_1.version == 1
    assert mock_config_entry_v1_1.minor_version == 2

    # Verify the entities have been migrated
    assert entity_registry.async_get_entity_id(
        "sensor", DOMAIN, "TEST123456789_ofa_orp_time"
    )
    assert entity_registry.async_get_entity_id(
        "sensor", DOMAIN, "TEST123456789_ofa_ph_time"
    )

    # Verify old unique IDs no longer exist
    assert not entity_registry.async_get_entity_id(
        "sensor", DOMAIN, "TEST123456789_ofa_orp_value"
    )
    assert not entity_registry.async_get_entity_id(
        "sensor", DOMAIN, "TEST123456789_ofa_ph_value"
    )

    # Verify entity that didn't need migration is unchanged
    assert (
        entity_registry.async_get_entity_id("sensor", DOMAIN, "TEST123456789_orp")
        == unchanged_entity.entity_id
    )