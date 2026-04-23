async def test_delete_many_async_uses_specialized_implementation(self):
        if (
            cache.delete_many.__func__ is not BaseCache.delete_many
            and cache.adelete_many.__func__ is BaseCache.adelete_many
        ):
            with mock.patch.object(cache, "delete_many") as mocked:
                mocked.__func__ = lambda x: x
                await cache.adelete_many({})
                mocked.assert_called_once()