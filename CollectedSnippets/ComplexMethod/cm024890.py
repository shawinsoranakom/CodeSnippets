async def test_platform_state_write_from_init_unique_id(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test platform state when an entity attempts to write from init.

    The outcome of this test is a bit illogical, when we no longer allow
    entities without platforms, attempts to write when state is NOT_ADDED
    will be blocked.
    """

    entry = entity_registry.async_get_or_create(
        "test", "test_platform", "5678", suggested_object_id="test"
    )
    assert entry.entity_id == "test.test"

    class MockEntity(entity.Entity):
        _attr_unique_id = "5678"

        def __init__(self, hass: HomeAssistant) -> None:
            self.entity_id = "test.test"
            self.hass = hass
            # The attempt to write when in state NOT_ADDED is not prevented because
            # the platform is not yet set
            assert self._platform_state == entity.EntityPlatformState.NOT_ADDED
            self._attr_state = "init"
            self.async_write_ha_state()
            assert hass.states.get("test.test").state == "init"

        async def async_added_to_hass(self):
            raise NotImplementedError("Should not be called")

        async def async_will_remove_from_hass(self):
            raise NotImplementedError("Should not be called")

    platform = MockEntityPlatform(hass, domain="test")
    ent = MockEntity(hass)
    assert ent._platform_state == entity.EntityPlatformState.NOT_ADDED
    await platform.async_add_entities([ent])
    assert hass.states.get("test.test").state == "init"
    assert ent._platform_state == entity.EntityPlatformState.REMOVED

    assert len(hass.states.async_all()) == 1

    # The early attempt to write is interpreted as a unique ID collision
    assert "Platform test_platform does not generate unique IDs." in caplog.text
    assert "Entity id already exists - ignoring: test.test" not in caplog.text