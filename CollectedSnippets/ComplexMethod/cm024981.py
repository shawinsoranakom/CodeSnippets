async def test_parallel_updates_sync_platform_updates_in_sequence(
    hass: HomeAssistant,
) -> None:
    """Test a sync platform is updated in sequence."""
    platform = MockPlatform()

    mock_platform(hass, "platform.test_domain", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    component._platforms = {}

    await component.async_setup({DOMAIN: {"platform": "platform"}})
    await hass.async_block_till_done()

    handle = list(component._platforms.values())[-1]
    updating = []
    peak_update_count = 0

    class SyncEntity(MockEntity):
        """Mock entity that has update."""

        def update(self):
            pass

        async def async_update_ha_state(self, *args: Any, **kwargs: Any) -> None:
            nonlocal peak_update_count
            updating.append(self.entity_id)
            await asyncio.sleep(0)
            peak_update_count = max(len(updating), peak_update_count)
            await asyncio.sleep(0)
            updating.remove(self.entity_id)

    entity1 = SyncEntity()
    entity2 = SyncEntity()
    entity3 = SyncEntity()

    await handle.async_add_entities([entity1, entity2, entity3])
    assert entity1.parallel_updates is not None
    assert entity1.parallel_updates._value == 1
    assert entity2.parallel_updates is not None
    assert entity2.parallel_updates._value == 1
    assert entity3.parallel_updates is not None
    assert entity3.parallel_updates._value == 1

    assert handle._update_in_sequence is True

    await handle._async_update_entity_states()
    assert peak_update_count == 1