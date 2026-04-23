async def test_async_async_request_call_with_lock(hass: HomeAssistant) -> None:
    """Test for async_requests_call works with a semaphore."""
    updates = []

    test_semaphore = asyncio.Semaphore(1)

    class AsyncEntity(entity.Entity):
        """Test entity."""

        def __init__(self, entity_id: str, lock: asyncio.Semaphore) -> None:
            """Initialize Async test entity."""
            self.entity_id = entity_id
            self.hass = hass
            self.parallel_updates = lock

        async def testhelper(self, count):
            """Helper function."""
            updates.append(count)

    ent_1 = AsyncEntity("light.test_1", test_semaphore)
    ent_2 = AsyncEntity("light.test_2", test_semaphore)

    try:
        assert test_semaphore.locked() is False
        await test_semaphore.acquire()
        assert test_semaphore.locked()

        job1 = ent_1.async_request_call(ent_1.testhelper(1))
        job2 = ent_2.async_request_call(ent_2.testhelper(2))

        hass.async_create_task(job1)
        hass.async_create_task(job2)

        assert len(updates) == 0
        assert updates == []
        assert test_semaphore._value == 0

        test_semaphore.release()

        while True:
            if len(updates) >= 2:
                break
            await asyncio.sleep(0)
    finally:
        test_semaphore.release()

    assert len(updates) == 2
    updates.sort()
    assert updates == [1, 2]