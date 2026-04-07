async def test_get_many_async_uses_specialized_implementation(self):
        if (
            cache.get_many.__func__ is not BaseCache.get_many
            and cache.aget_many.__func__ is BaseCache.aget_many
        ):
            with mock.patch.object(cache, "get_many") as mocked:
                mocked.__func__ = lambda x: x
                await cache.aget_many({})
                mocked.assert_called_once()