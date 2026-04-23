async def test_async_remove_twice(hass: HomeAssistant) -> None:
    """Test removing an entity twice only cleans up once."""
    result = []

    class MockEntity(entity.Entity):
        def __init__(self) -> None:
            self.remove_calls = []

        async def async_will_remove_from_hass(self) -> None:
            self.remove_calls.append(None)

    platform = MockEntityPlatform(hass, domain="test")
    ent = MockEntity()
    ent.hass = hass
    ent.entity_id = "test.test"
    ent.async_on_remove(lambda: result.append(1))
    await platform.async_add_entities([ent])
    assert hass.states.get("test.test").state == STATE_UNKNOWN

    await ent.async_remove()
    assert len(result) == 1
    assert len(ent.remove_calls) == 1
    assert ent._platform_state == entity.EntityPlatformState.REMOVED

    await ent.async_remove()
    assert len(result) == 1
    assert len(ent.remove_calls) == 1
    assert ent._platform_state == entity.EntityPlatformState.REMOVED