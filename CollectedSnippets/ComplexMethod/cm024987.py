async def test_setup_entry_with_entities_that_block_forever(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    entity_registry: er.EntityRegistry,
    update_before_add: bool,
) -> None:
    """Test we cancel adding entities when we reach the timeout."""

    async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setup entry method."""
        async_add_entities(
            [MockBlockingEntity(name="test1", unique_id="unique")],
            update_before_add=update_before_add,
        )

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(entry_id="super-mock-id")
    config_entry.add_to_hass(hass)
    platform = MockEntityPlatform(
        hass, platform_name=config_entry.domain, platform=platform
    )

    with (
        patch.object(entity_platform, "SLOW_ADD_ENTITY_MAX_WAIT", 0.01),
        patch.object(entity_platform, "SLOW_ADD_MIN_TIMEOUT", 0.01),
    ):
        assert await platform.async_setup_entry(config_entry)
        await hass.async_block_till_done()
    full_name = f"{config_entry.domain}.{platform.domain}"
    assert full_name in hass.config.components
    assert len(hass.states.async_entity_ids()) == 0
    assert len(entity_registry.entities) == 1
    assert "Timed out adding entities" in caplog.text
    assert "test_domain.test1" in caplog.text
    assert "test_domain" in caplog.text
    assert "test" in caplog.text