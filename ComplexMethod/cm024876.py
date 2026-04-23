async def test_disabled_in_entity_registry(hass: HomeAssistant) -> None:
    """Test entity is removed if we disable entity registry entry."""
    entry = RegistryEntryWithDefaults(
        entity_id="hello.world",
        unique_id="test-unique-id",
        platform="test-platform",
        disabled_by=None,
    )
    registry = mock_registry(hass, {"hello.world": entry})

    ent = entity.Entity()
    ent.hass = hass
    ent.entity_id = "hello.world"
    ent.registry_entry = entry
    assert ent.enabled is True

    ent.add_to_platform_start(hass, MagicMock(platform_name="test-platform"), None)
    await ent.add_to_platform_finish()
    assert hass.states.get("hello.world") is not None

    entry2 = registry.async_update_entity(
        "hello.world", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()
    assert entry2 != entry
    assert ent.registry_entry == entry2
    assert ent.enabled is False
    assert hass.states.get("hello.world") is None

    entry3 = registry.async_update_entity("hello.world", disabled_by=None)
    await hass.async_block_till_done()
    assert entry3 != entry2
    # Entry is no longer updated, entity is no longer tracking changes
    assert ent.registry_entry == entry2