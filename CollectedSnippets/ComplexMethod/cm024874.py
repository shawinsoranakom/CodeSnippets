async def test_async_parallel_updates_with_two(hass: HomeAssistant) -> None:
    """Test parallel updates with 2 (parallel)."""
    updates = []
    test_lock = asyncio.Lock()
    test_semaphore = asyncio.Semaphore(2)

    class AsyncEntity(entity.Entity):
        """Test entity."""

        def __init__(self, entity_id: str, count: int) -> None:
            """Initialize Async test entity."""
            self.entity_id = entity_id
            self.hass = hass
            self._count = count
            self.parallel_updates = test_semaphore

        async def async_update(self) -> None:
            """Test update."""
            updates.append(self._count)
            await test_lock.acquire()

    ent_1 = AsyncEntity("sensor.test_1", 1)
    ent_2 = AsyncEntity("sensor.test_2", 2)
    ent_3 = AsyncEntity("sensor.test_3", 3)
    ent_4 = AsyncEntity("sensor.test_4", 4)

    await test_lock.acquire()

    try:
        ent_1.async_schedule_update_ha_state(True)
        ent_2.async_schedule_update_ha_state(True)
        ent_3.async_schedule_update_ha_state(True)
        ent_4.async_schedule_update_ha_state(True)

        while True:
            if len(updates) >= 2:
                break
            await asyncio.sleep(0)

        assert len(updates) == 2
        assert updates == [1, 2]

        updates.clear()
        test_lock.release()
        await asyncio.sleep(0)
        test_lock.release()
        await asyncio.sleep(0)

        while True:
            if len(updates) >= 2:
                break
            await asyncio.sleep(0)

        assert len(updates) == 2
        assert updates == [3, 4]

        updates.clear()
        test_lock.release()
        await asyncio.sleep(0)
        test_lock.release()
        await asyncio.sleep(0)
    finally:
        # we may have more than one lock need to release in case test failed
        for _ in updates:
            test_lock.release()
            await asyncio.sleep(0)
        test_lock.release()