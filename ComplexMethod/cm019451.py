async def test_migrate_uuid(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    emoncms_client: AsyncMock,
) -> None:
    """Test migration from home assistant uuid to emoncms uuid."""
    config_entry.add_to_hass(hass)
    assert config_entry.unique_id is None
    for _, feed in enumerate(FEEDS):
        entity_registry.async_get_or_create(
            Platform.SENSOR,
            DOMAIN,
            f"{config_entry.entry_id}-{feed[FEED_ID]}",
            config_entry=config_entry,
            suggested_object_id=f"{DOMAIN}_{feed[FEED_NAME]}",
        )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    emoncms_uuid = emoncms_client.async_get_uuid.return_value
    assert config_entry.unique_id == emoncms_uuid
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    for nb, feed in enumerate(FEEDS):
        assert entity_entries[nb].unique_id == f"{emoncms_uuid}-{feed[FEED_ID]}"
        assert (
            entity_entries[nb].previous_unique_id
            == f"{config_entry.entry_id}-{feed[FEED_ID]}"
        )