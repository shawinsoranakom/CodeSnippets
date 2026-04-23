async def test_update_unique_id_existing(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
    mock_ring_client,
) -> None:
    """Test unique_id update of integration."""
    old_unique_id = 123456
    entry = MockConfigEntry(
        title="Ring",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "foo@bar.com",
            "token": {"access_token": "mock-token"},
        },
        unique_id="foo@bar.com",
        minor_version=1,
    )
    entry.add_to_hass(hass)

    entity = entity_registry.async_get_or_create(
        domain=CAMERA_DOMAIN,
        platform=DOMAIN,
        unique_id=old_unique_id,
        config_entry=entry,
    )
    entity_existing = entity_registry.async_get_or_create(
        domain=CAMERA_DOMAIN,
        platform=DOMAIN,
        unique_id=str(old_unique_id),
        config_entry=entry,
    )
    assert entity.unique_id == old_unique_id
    assert entity_existing.unique_id == str(old_unique_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_not_migrated = entity_registry.async_get(entity.entity_id)
    entity_existing = entity_registry.async_get(entity_existing.entity_id)
    assert entity_not_migrated
    assert entity_existing
    assert entity_not_migrated.unique_id == old_unique_id
    assert (
        f"Cannot migrate to unique_id '{old_unique_id}', "
        f"already exists for '{entity_existing.entity_id}', "
        "You may have to delete unavailable ring entities"
    ) in caplog.text
    assert entry.minor_version == CONF_CONFIG_ENTRY_MINOR_VERSION