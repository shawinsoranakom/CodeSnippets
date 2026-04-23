async def test_dont_migrate_unique_ids(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    entitydata: dict,
    old_unique_id: str,
    new_unique_id: str,
    station_id: str,
) -> None:
    """Test successful migration of entity unique_ids."""
    FIXTURE_CONFIG_ENTRY["data"][CONF_STATION_ID] = station_id
    mock_config_entry = MockConfigEntry(**FIXTURE_CONFIG_ENTRY)
    mock_config_entry.add_to_hass(hass)

    # create existing entry with new_unique_id
    existing_entity = entity_registry.async_get_or_create(
        WEATHER_DOMAIN,
        DOMAIN,
        unique_id=TEST_STATION_ID,
        suggested_object_id=f"Zamg {TEST_STATION_NAME}",
        config_entry=mock_config_entry,
    )

    entity: er.RegistryEntry = entity_registry.async_get_or_create(
        **entitydata,
        config_entry=mock_config_entry,
    )

    assert entity.unique_id == old_unique_id

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_migrated = entity_registry.async_get(entity.entity_id)
    assert entity_migrated
    assert entity_migrated.unique_id == old_unique_id

    entity_not_changed = entity_registry.async_get(existing_entity.entity_id)
    assert entity_not_changed
    assert entity_not_changed.unique_id == new_unique_id

    assert entity_migrated != entity_not_changed