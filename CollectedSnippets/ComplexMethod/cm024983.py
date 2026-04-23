async def test_setup_entry(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test we can setup an entry."""

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setup entry method."""
        async_add_entities([MockEntity(name="test1", unique_id="unique1")])
        async_add_entities(
            [MockEntity(name="test2", unique_id="unique2")],
            config_subentry_id="mock-subentry-id-1",
        )

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(
        entry_id="super-mock-id",
        subentries_data=(
            ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ),
    )
    config_entry.add_to_hass(hass)
    entity_platform = MockEntityPlatform(
        hass, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await hass.async_block_till_done()
    full_name = f"{config_entry.domain}.{entity_platform.domain}"
    assert full_name in hass.config.components
    assert len(hass.states.async_entity_ids()) == 2
    assert len(entity_registry.entities) == 2

    entity_registry_entry = entity_registry.entities["test_domain.test1"]
    assert entity_registry_entry.config_entry_id == "super-mock-id"
    assert entity_registry_entry.config_subentry_id is None

    entity_registry_entry = entity_registry.entities["test_domain.test2"]
    assert entity_registry_entry.config_entry_id == "super-mock-id"
    assert entity_registry_entry.config_subentry_id == "mock-subentry-id-1"