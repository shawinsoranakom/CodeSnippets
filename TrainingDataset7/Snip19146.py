async def test_get_or_set_async_uses_specialized_implementation(self):
        await cache.aset("key", "value")
        if (
            cache.get_or_set.__func__ is not BaseCache.get_or_set
            and cache.aget_or_set.__func__ is BaseCache.aget_or_set
        ):
            with mock.patch.object(cache, "get_or_set") as mocked:
                mocked.__func__ = lambda x: x
                await cache.aget_or_set("key")
                mocked.assert_called_once()