async def test_change_entity_id_config_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    config_subentry_id: str | None,
) -> None:
    """Test changing entity id does not effect the config entry."""

    class MockEntity(entity.Entity):
        _attr_unique_id = "5678"

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setup entry method."""
        async_add_entities([MockEntity()], config_subentry_id=config_subentry_id)

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(
        entry_id="super-mock-id",
        subentries_data=[
            ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    config_entry.add_to_hass(hass)
    entity_platform = MockEntityPlatform(
        hass, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await hass.async_block_till_done()

    ent = entity_registry.async_get(next(iter(hass.states.async_entity_ids())))
    assert ent == snapshot
    # The snapshot check asserts on any (sub)entry ID
    assert ent.config_entry_id == config_entry.entry_id
    assert ent.config_subentry_id == config_subentry_id

    state = hass.states.async_all()[0]
    assert state == snapshot

    entity_registry.async_update_entity(
        ent.entity_id, new_entity_id="test_domain.test2"
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    new_ent = entity_registry.async_get("test_domain.test2")
    assert new_ent == snapshot
    # The snapshot check asserts on any (sub)entry ID
    assert new_ent.config_entry_id == config_entry.entry_id
    assert new_ent.config_subentry_id == config_subentry_id

    new_state = hass.states.get("test_domain.test2")
    assert new_state == snapshot