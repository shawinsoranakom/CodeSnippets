async def test_has_key_async_uses_specialized_implementation(self):
        await cache.aset("key", "value")
        if (
            cache.has_key.__func__ is not BaseCache.has_key
            and cache.ahas_key.__func__ is BaseCache.ahas_key
        ):
            with mock.patch.object(cache, "has_key") as mocked:
                mocked.__func__ = lambda x: x
                await cache.ahas_key("key")
                mocked.assert_called_once()