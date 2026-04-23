async def test_set_many_async_uses_specialized_implementation(self):
        if (
            cache.set_many.__func__ is not BaseCache.set_many
            and cache.aset_many.__func__ is BaseCache.aset_many
        ):
            with mock.patch.object(cache, "set_many") as mocked:
                mocked.__func__ = lambda x: x
                await cache.aset_many({})
                mocked.assert_called_once()